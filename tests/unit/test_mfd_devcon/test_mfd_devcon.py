# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `mfd_devcon` package."""

from textwrap import dedent
from pathlib import Path

import pytest
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName

from mfd_connect.util import rpc_copy_utils
from mfd_devcon import Devcon
from mfd_devcon.exceptions import DevconNotAvailable, DevconException, DevconExecutionError
from mfd_devcon.parser import DevconHwids, DevconDriverNodes, DevconDriverFiles, DevconDevices, DevconResources


class TestMfdDevcon:
    @pytest.fixture()
    def devcon(self, mocker):
        mocker.patch(
            "mfd_connect.util.rpc_copy_utils.copy",
            mocker.create_autospec(rpc_copy_utils.copy),
        )
        mocker.patch("mfd_devcon.Devcon.check_if_available", mocker.create_autospec(Devcon.check_if_available))
        mocker.patch("mfd_devcon.Devcon.get_version", mocker.create_autospec(Devcon.get_version, return_value="N/A"))
        mocker.patch(
            "mfd_devcon.Devcon._get_tool_exec_factory",
            mocker.create_autospec(Devcon._get_tool_exec_factory, return_value="devcon_x64.exe"),
        )
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.WINDOWS
        conn.path = mocker.create_autospec(Path)
        devcon = Devcon(connection=conn)
        mocker.stopall()
        return devcon

    @pytest.fixture()
    def devcon_with_exe_path(self, mocker):
        mocker.patch("mfd_devcon.Devcon.check_if_available", mocker.create_autospec(Devcon.check_if_available))
        mocker.patch("mfd_devcon.Devcon.get_version", mocker.create_autospec(Devcon.get_version, return_value="N/A"))
        mocker.patch(
            "mfd_devcon.Devcon._get_tool_exec_factory",
            mocker.create_autospec(Devcon._get_tool_exec_factory, return_value="devcon_x64.exe"),
        )
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.WINDOWS
        conn.path = mocker.create_autospec(Path)
        devcon = Devcon(connection=conn, absolute_path_to_binary_dir="C:\\devcon\\")
        mocker.stopall()
        return devcon

    def test_check_if_available(self, devcon_with_exe_path):
        devcon_with_exe_path._connection.execute_command.return_value.return_code = 0
        devcon_with_exe_path.check_if_available()

    def test_check_if_available_when_tool_not_found(self, devcon):
        devcon._connection.execute_command.side_effect = DevconNotAvailable(returncode=1, cmd="")
        with pytest.raises(DevconNotAvailable):
            devcon.check_if_available()

    def test_get_version(self, devcon):
        assert devcon.get_version() == "N/A"

    def test_enable_devices_with_device_id(self, devcon):
        output = dedent(
            r"""\
        PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63: Enabled
        1 device(s) are enabled.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe /r enable "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        devcon.enable_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63", reboot=True)

    def test_enable_devices_with_pattern(self, devcon_with_exe_path):
        output = dedent(
            r"""\
        USB\VID_413C&PID_A001\0123456789                            : Enabled
        USB\VID_14DD&PID_1007\PQ203048400000007                     : Enabled
        PCI\VEN_8086&DEV_8D26&SUBSYS_06001028&REV_05\3&3259BAD1&0&E8: Enabled
        USB\ROOT_HUB20\4&57D8877&0                                  : Enabled
        USB\ROOT_HUB20\4&710B31&0                                   : Enabled
        USB\VID_8087&PID_800A\5&30A468B4&0&1                        : Enabled
        USB\VID_8087&PID_8002\5&3FFC515&0&1                         : Enabled
        PCI\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\3&3259BAD1&0&D0: Enabled
        8 device(s) are enabled.
            """
        )
        devcon_with_exe_path._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe enable =usb", stdout=output, return_code=0, stderr=""
        )
        devcon_with_exe_path.enable_devices(pattern="=usb")

    def test_enable_devices_with_execution_error(self, devcon):
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=1,
            cmd=r'C:\devcon\devcon_x64.exe enable "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63"',
        )
        with pytest.raises(DevconExecutionError):
            devcon.enable_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63")

    def test_enable_devices_with_known_errors(self, devcon_with_exe_path):
        output = dedent(
            """\
        No matching devices found.
            """
        )
        devcon_with_exe_path._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe enable "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        with pytest.raises(DevconException, match="No matching devices found"):
            devcon_with_exe_path.enable_devices(
                device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6"
            )

    def test_disable_devices_with_device_id(self, devcon):
        output = dedent(
            r"""\
        PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63: Disabled
        1 device(s) are disabled.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe /r disable "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        devcon.disable_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63", reboot=True)

    def test_disable_devices_with_pattern(self, devcon):
        output = dedent(
            r"""\
        USB\VID_413C&PID_A001\0123456789                            : Disabled
        USB\VID_14DD&PID_1007\PQ203048400000007                     : Disabled
        PCI\VEN_8086&DEV_8D26&SUBSYS_06001028&REV_05\3&3259BAD1&0&E8: Disabled
        USB\ROOT_HUB20\4&57D8877&0                                  : Disabled
        USB\ROOT_HUB20\4&710B31&0                                   : Disabled
        USB\VID_8087&PID_800A\5&30A468B4&0&1                        : Disabled
        USB\VID_8087&PID_8002\5&3FFC515&0&1                         : Disabled
        PCI\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\3&3259BAD1&0&D0: Disabled
        8 device(s) are disabled.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe disable =usb", stdout=output, return_code=0, stderr=""
        )
        devcon.disable_devices(pattern="=usb")

    def test_disable_devices_with_execution_error(self, devcon):
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=1,
            cmd=r'C:\devcon\devcon_x64.exe disable "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63"',
        )
        with pytest.raises(DevconExecutionError):
            devcon.disable_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63")

    def test_disable_devices_with_known_errors(self, devcon):
        output = dedent(
            """\
        No matching devices found.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe disable "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        with pytest.raises(DevconException, match="No matching devices found"):
            devcon.disable_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6")

    def test_rescan_devices(self, devcon):
        output = dedent(
            """\
        Scanning for new hardware.
        Scanning completed.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe rescan", stdout=output, return_code=0, stderr=""
        )
        devcon.rescan_devices()

    def test_rescan_devices_with_error(self, devcon):
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=1, cmd=r"C:\devcon\devcon_x64.exe rescan"
        )
        with pytest.raises(DevconExecutionError):
            devcon.rescan_devices()

    def test_remove_devices_with_device_id(self, devcon):
        output = dedent(
            r"""\
        PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63: Removed
        1 device(s) removed.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe /r remove "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        devcon.remove_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63", reboot=True)

    def test_remove_devices_with_pattern(self, devcon):
        output = dedent(
            r"""\
        USB\ROOT_HUB\4&2A40B465&0 : Removed
        USB\ROOT_HUB\4&7EFA360&0 : Removed
        USB\VID_045E&PID_0039\5&29F428A4&0&2 : Removed
        3 device(s) removed.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe remove @usb\*", stdout=output, return_code=0, stderr=""
        )
        devcon.remove_devices(pattern=r"@usb\*")

    def test_remove_devices_with_execution_error(self, devcon):
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=1, cmd=r"C:\devcon\devcon_x64.exe remove @usb\*"
        )
        with pytest.raises(DevconExecutionError):
            devcon.remove_devices(pattern=r"@usb\*")

    def test_remove_devices_with_known_errors(self, devcon):
        output = dedent(
            """\
        No matching devices found.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe remove "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        with pytest.raises(DevconException, match="No matching devices found"):
            devcon.remove_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6")

    def test_update_drivers(self, devcon):
        output = dedent(
            r"""\ Updating drivers for PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200 from
             C:\windows\inf\test.inf. Drivers updated successfully. """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe /r update C:\windows\inf\test.inf "
            r'"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        devcon.update_drivers(
            device_id=r"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200",
            inf_file=r"C:\windows\inf\test.inf",
            reboot=True,
        )

    def test_update_drivers_with_error(self, devcon):
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=2,
            cmd=r"C:\devcon\devcon_x64.exe update C:\windows\inf\test.inf "
            r'"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200"',
        )
        with pytest.raises(DevconExecutionError):
            devcon.update_drivers(
                device_id=r"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200",
                inf_file=r"C:\windows\inf\test.inf",
            )

    def test_restart_devices_with_device_id(self, devcon):
        output = dedent(
            r"""\
        PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200: Restarted
        1 device(s) restarted.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe /r restart "
            r'"@PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        devcon.restart_devices(
            device_id=r"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200", reboot=True
        )

    def test_restart_devices_with_pattern(self, devcon):
        output = dedent(
            r"""\
        PCI\VEN_8086&DEV_2FB1&SUBSYS_2FB18086&REV_02\3&1C6B4348&0&A1: Restarted
        PCI\VEN_8086&DEV_2FB3&SUBSYS_2FB38086&REV_02\3&1C6B4348&0&A3: Restarted
        PCI\VEN_8086&DEV_2FBD&SUBSYS_00000000&REV_02\3&103A9D54&0&A5: Restarted
        PCI\VEN_8086&DEV_2F1D&SUBSYS_2F1D8086&REV_02\3&1C6B4348&0&80: Restarted
        PCI\VEN_8086&DEV_2F1F&SUBSYS_2F1F8086&REV_02\3&1C6B4348&0&87: Restarted
        PCI\VEN_8086&DEV_2FE1&SUBSYS_2FE18086&REV_02\3&1C6B4348&0&61: Restarted
        PCI\VEN_8086&DEV_2F78&SUBSYS_2F788086&REV_02\3&1C6B4348&0&96: Restarted
        PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63: Restarted
        8 device(s) restarted.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r"C:\devcon\devcon_x64.exe restart pci*", stdout=output, return_code=0, stderr=""
        )
        devcon.restart_devices(pattern="pci*")

    def test_restart_devices_with_execution_error(self, devcon):
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=1,
            cmd=r'C:\devcon\devcon_x64.exe restart "@PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200"',
        )
        with pytest.raises(DevconExecutionError):
            devcon.restart_devices(device_id=r"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200")

    def test_restart_devices_with_known_errors(self, devcon):
        output = dedent(
            """\
        No matching devices found.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=r'C:\devcon\devcon_x64.exe restart "@PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        with pytest.raises(DevconException, match="No matching devices found"):
            devcon.restart_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&6")

    def test_get_hwids(self, devcon):
        output = dedent(
            """\
        ACPI_HAL\\PNP0C08\\0
            Name: Microsoft ACPI-Compliant System
            Hardware IDs:
                ACPI_HAL\\PNP0C08
                *PNP0C08
        HTREE\\ROOT\\0
            No hardware/compatible IDs found for this device.
        ROOT\\BASICRENDER\\0000
            Name: Microsoft Basic Render Driver
            Hardware IDs:
                ROOT\\BasicRender
        PCI\\VEN_8086&DEV_2FE1&SUBSYS_2FE18086&REV_02\\3&103A9D54&0&61
            Name: Base System Device
            Hardware IDs:
                PCI\\VEN_8086&DEV_2FE1&SUBSYS_2FE18086&REV_02
                PCI\\VEN_8086&DEV_2FE1&SUBSYS_2FE18086
                PCI\\VEN_8086&DEV_2FE1&CC_088000
                PCI\\VEN_8086&DEV_2FE1&CC_0880
            Compatible IDs:
                PCI\\VEN_8086&DEV_2FE1&REV_02
                PCI\\VEN_8086&DEV_2FE1
                PCI\\VEN_8086&CC_088000
                PCI\\VEN_8086&CC_0880
                PCI\\VEN_8086
                PCI\\CC_088000
                PCI\\CC_0880
        4 matching device(s) found.
            """
        )
        expected_output = [
            DevconHwids(
                device_pnp="ACPI_HAL\\PNP0C08\\0",
                name="Microsoft ACPI-Compliant System",
                hardware_ids=["ACPI_HAL\\PNP0C08", "*PNP0C08"],
                compatible_ids=[],
            ),
            DevconHwids(device_pnp="HTREE\\ROOT\\0", name="", hardware_ids=[], compatible_ids=[]),
            DevconHwids(
                device_pnp="ROOT\\BASICRENDER\\0000",
                name="Microsoft Basic Render Driver",
                hardware_ids=["ROOT\\BasicRender"],
                compatible_ids=[],
            ),
            DevconHwids(
                device_pnp="PCI\\VEN_8086&DEV_2FE1&SUBSYS_2FE18086&REV_02\\3&103A9D54&0&61",
                name="Base System Device",
                hardware_ids=[
                    "PCI\\VEN_8086&DEV_2FE1&SUBSYS_2FE18086&REV_02",
                    "PCI\\VEN_8086&DEV_2FE1&SUBSYS_2FE18086",
                    "PCI\\VEN_8086&DEV_2FE1&CC_088000",
                    "PCI\\VEN_8086&DEV_2FE1&CC_0880",
                ],
                compatible_ids=[
                    "PCI\\VEN_8086&DEV_2FE1&REV_02",
                    "PCI\\VEN_8086&DEV_2FE1",
                    "PCI\\VEN_8086&CC_088000",
                    "PCI\\VEN_8086&CC_0880",
                    "PCI\\VEN_8086",
                    "PCI\\CC_088000",
                    "PCI\\CC_0880",
                ],
            ),
        ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.get_hwids(pattern="=net") == expected_output

    def test_get_drivernodes(self, devcon):
        output = dedent(
            """\
        ACPI\\FIXEDBUTTON\\2&DABA3FF&0
            Name: ACPI Fixed Feature Button
        Driver node #0:
            Inf file is C:\\windows\\INF\\machine.inf
            Inf section is NO_DRV
            Driver description is ACPI Fixed Feature Button
            Manufacturer name is (Standard system devices)
            Provider name is Microsoft
            Driver date is 6/21/2006
            Driver version is 10.0.22000.1
            Driver node rank is 16711680
            Driver node flags are 00142044
                Inf is digitally signed
        USB4\\VIRTUAL_POWER_PDO\\4&26DBF7B8&0&0
            Name: USB4 Virtual power coordination device
            No driver nodes found for this device.
        PCI\\VEN_8086&DEV_51EF&SUBSYS_897F103C&REV_01\\3&11583659&0&A2
            Name: Intel(R) Shared SRAM - 51EF
        Driver node #0:
            Inf file is C:\\windows\\INF\\machine.inf
            Inf section is NO_DRV
            Driver description is PCI standard RAM Controller
            Manufacturer name is (Standard system devices)
            Provider name is Microsoft
            Driver date is 6/21/2006
            Driver version is 10.0.22000.1
            Driver node rank is 16719878
            Driver node flags are 00102044
                Inf is digitally signed
        Driver node #1:
            Inf file is C:\\windows\\INF\\oem104.inf
            Inf section is Needs_NO_DRV
            Driver description is Intel(R) Shared SRAM - 51EF
            Manufacturer name is INTEL
            Provider name is INTEL
            Driver date is 7/18/1968
            Driver version is 10.1.36.7
            Driver node rank is 16719873
            Driver node flags are 00042044
                Inf is digitally signed
        3 matching device(s) found.
            """
        )
        expected_output = [
            DevconDriverNodes(
                device_pnp="ACPI\\FIXEDBUTTON\\2&DABA3FF&0",
                name="ACPI Fixed Feature Button",
                driver_nodes={
                    "0": {
                        "inf_file": "C:\\windows\\INF\\machine.inf",
                        "inf_section": "NO_DRV",
                        "driver_desc": "ACPI Fixed Feature Button",
                        "manufacturer_name": "(Standard system devices)",
                        "provider_name": "Microsoft",
                        "driver_date": "6/21/2006",
                        "driver_version": "10.0.22000.1",
                        "driver_node_rank": "16711680",
                        "driver_node_flags": "00142044",
                    }
                },
            ),
            DevconDriverNodes(
                device_pnp="USB4\\VIRTUAL_POWER_PDO\\4&26DBF7B8&0&0",
                name="USB4 Virtual power coordination device",
                driver_nodes={},
            ),
            DevconDriverNodes(
                device_pnp="PCI\\VEN_8086&DEV_51EF&SUBSYS_897F103C&REV_01\\3&11583659&0&A2",
                name="Intel(R) Shared SRAM - 51EF",
                driver_nodes={
                    "0": {
                        "inf_file": "C:\\windows\\INF\\machine.inf",
                        "inf_section": "NO_DRV",
                        "driver_desc": "PCI standard RAM Controller",
                        "manufacturer_name": "(Standard system devices)",
                        "provider_name": "Microsoft",
                        "driver_date": "6/21/2006",
                        "driver_version": "10.0.22000.1",
                        "driver_node_rank": "16719878",
                        "driver_node_flags": "00102044",
                    },
                    "1": {
                        "inf_file": "C:\\windows\\INF\\oem104.inf",
                        "inf_section": "Needs_NO_DRV",
                        "driver_desc": "Intel(R) Shared SRAM - 51EF",
                        "manufacturer_name": "INTEL",
                        "provider_name": "INTEL",
                        "driver_date": "7/18/1968",
                        "driver_version": "10.1.36.7",
                        "driver_node_rank": "16719873",
                        "driver_node_flags": "00042044",
                    },
                },
            ),
        ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.get_drivernodes(pattern="=net") == expected_output

    def test_get_driverfiles(self, devcon):
        output = dedent(
            """\
            PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710
                Name: Intel(R) Ethernet Network Adapter E810-C-Q2 #8
                Driver installed from C:\\Windows\\INF\\oem5.inf [F1592]. 3 file(s) used by driver:
                    C:\\Windows\\System32\\DriverStore\\FileRepository\\icea.inf_amd64_1788bf38a7bdc1f8\\icea.sys
                    C:\\Windows\\System32\\DriverStore\\FileRepository\\icea.inf_amd64_1788bf38a7bdc1f8\\manifest_icea.man
                    C:\\Windows\\System32\\DriverStore\\FileRepository\\icea.inf_amd64_1788bf38a7bdc1f8\\iceamsg.dll
            SWD\\MSRRAS\\MS_PPPOEMINIPORT
                Name: WAN Miniport (PPPOE)
                Driver installed from C:\\Windows\\INF\\metrasa.inf [Ndi-Mp-Pppoe]. The driver is not using any files.
            2 matching device(s) found.
            """
        )
        expected_output = [
            DevconDriverFiles(
                device_pnp="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710",
                name="Intel(R) Ethernet Network Adapter E810-C-Q2 #8",
                installed_from="C:\\Windows\\INF\\oem5.inf [F1592]",
                driver_files=[
                    "C:\\Windows\\System32\\DriverStore\\FileRepository\\icea.inf_amd64_1788bf38a7bdc1f8\\icea.sys",
                    "C:\\Windows\\System32\\DriverStore\\FileRepository\\icea.inf_amd64_1788bf38a7bdc1f8\\"
                    "manifest_icea.man",
                    "C:\\Windows\\System32\\DriverStore\\FileRepository\\icea.inf_amd64_1788bf38a7bdc1f8\\iceamsg.dll",
                ],
            ),
            DevconDriverFiles(
                device_pnp="SWD\\MSRRAS\\MS_PPPOEMINIPORT",
                name="WAN Miniport (PPPOE)",
                installed_from="C:\\Windows\\INF\\metrasa.inf [Ndi-Mp-Pppoe]",
                driver_files=[],
            ),
        ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.get_driverfiles(pattern="=net") == expected_output

    def test_find_devices(self, devcon):
        output = dedent(
            """\
        PCI\\VEN_8086&DEV_2F28&SUBSYS_00000000&REV_02\\3&3259BAD1&0&28: Base System Device
        PCI\\VEN_8086&DEV_2F1F&SUBSYS_2F1F8086&REV_02\\3&103A9D54&0&87: Base System Device
        ACPI_HAL\\PNP0C08\\0                                          : Microsoft ACPI-Compliant System
        HTREE\\ROOT\\0
        ROOT\\BASICRENDER\\0000                                       : Microsoft Basic Render Driver
        5 matching device(s) found.
            """
        )
        expected_output = [
            DevconDevices(
                device_instance_id="PCI\\VEN_8086&DEV_2F28&SUBSYS_00000000&REV_02\\3&3259BAD1&0&28",
                device_desc="Base System Device",
            ),
            DevconDevices(
                device_instance_id="PCI\\VEN_8086&DEV_2F1F&SUBSYS_2F1F8086&REV_02\\3&103A9D54&0&87",
                device_desc="Base System Device",
            ),
            DevconDevices(device_instance_id="ACPI_HAL\\PNP0C08\\0", device_desc="Microsoft ACPI-Compliant System"),
            DevconDevices(device_instance_id="HTREE\\ROOT\\0", device_desc=""),
            DevconDevices(device_instance_id="ROOT\\BASICRENDER\\0000", device_desc="Microsoft Basic Render Driver"),
        ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.find_devices(pattern="*") == expected_output

    def test_listclass(self, devcon):
        output = dedent(
            """\
        Listing 2 devices in setup class "Ports" (Ports (COM & LPT)).
        ACPI\\PNP0501\\1                                              : Communications Port (COM1)
        ACPI\\PNP0501\\2                                              : Communications Port (COM1)
            """
        )
        expected_output = [
            DevconDevices(device_instance_id="ACPI\\PNP0501\\1", device_desc="Communications Port (COM1)"),
            DevconDevices(device_instance_id="ACPI\\PNP0501\\2", device_desc="Communications Port (COM1)"),
        ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.listclass(class_name="ports") == expected_output

    def test_listclass_with_error_no_class(self, devcon):
        output = dedent(
            """\
        There is no "network" setup class on the local machine.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        e = 'There is no "network" setup class'
        with pytest.raises(DevconException, match=f"Error while running devcon command: {e}"):
            devcon.listclass(class_name="network")

    def test_listclass_with_error_no_devices_in_class(self, devcon):
        output = dedent(
            """\
        There are no devices in setup class "Printer" (Printers).
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        with pytest.raises(DevconException, match="There are no devices in setup class"):
            devcon.listclass(class_name="printer")

    def test_get_resources(self, devcon):
        output = dedent(
            """\
        PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0
            Name: Standard Enhanced PCI to USB Host Controller
            Device is currently using the following resources:
                MEM : 91e03000-91e033ff
                IRQ : 18
        ROOT\\SYSTEM\\0000
            Name: Plug and Play Software Device Enumerator
            Device is not using any resources.
        PCI\\VEN_8086&DEV_2FB1&SUBSYS_2FB18086&REV_02\\3&1C6B4348&0&A1
            Name: Base System Device
            Device has no reserved resources.
        3 matching device(s) found.
            """
        )
        expected_output = [
            DevconResources(
                device_pnp="PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0",
                name="Standard Enhanced PCI to USB Host Controller",
                resources=["MEM : 91e03000-91e033ff", "IRQ : 18"],
            ),
            DevconResources(
                device_pnp="ROOT\\SYSTEM\\0000", name="Plug and Play Software Device Enumerator", resources=[]
            ),
            DevconResources(
                device_pnp="PCI\\VEN_8086&DEV_2FB1&SUBSYS_2FB18086&REV_02\\3&1C6B4348&0&A1",
                name="Base System Device",
                resources=[],
            ),
        ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.get_resources(pattern="*") == expected_output

    @pytest.mark.parametrize("resource_filter", ["irq", "mem"])
    def test_get_resources_with_resource_filter(self, devcon, resource_filter):
        output = dedent(
            """\
        PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0
            Name: Standard Enhanced PCI to USB Host Controller
            Device is currently using the following resources:
                MEM : 91e03000-91e033ff
                IRQ : 18
        ROOT\\SYSTEM\\0000
            Name: Plug and Play Software Device Enumerator
            Device is not using any resources.
        PCI\\VEN_8086&DEV_2FB1&SUBSYS_2FB18086&REV_02\\3&1C6B4348&0&A1
            Name: Base System Device
            Device has no reserved resources.
        3 matching device(s) found.
            """
        )
        if resource_filter == "irq":
            expected_output = [
                DevconResources(
                    device_pnp="PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0",
                    name="Standard Enhanced PCI to USB Host Controller",
                    resources=["IRQ : 18"],
                ),
                DevconResources(
                    device_pnp="ROOT\\SYSTEM\\0000", name="Plug and Play Software Device Enumerator", resources=[]
                ),
                DevconResources(
                    device_pnp="PCI\\VEN_8086&DEV_2FB1&SUBSYS_2FB18086&REV_02\\3&1C6B4348&0&A1",
                    name="Base System Device",
                    resources=[],
                ),
            ]
        else:
            expected_output = [
                DevconResources(
                    device_pnp="PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0",
                    name="Standard Enhanced PCI to USB Host Controller",
                    resources=["MEM : 91e03000-91e033ff"],
                ),
                DevconResources(
                    device_pnp="ROOT\\SYSTEM\\0000", name="Plug and Play Software Device Enumerator", resources=[]
                ),
                DevconResources(
                    device_pnp="PCI\\VEN_8086&DEV_2FB1&SUBSYS_2FB18086&REV_02\\3&1C6B4348&0&A1",
                    name="Base System Device",
                    resources=[],
                ),
            ]
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.get_resources(pattern="*", resource_filter=resource_filter) == expected_output

    @pytest.mark.parametrize("command", ["hwids", "find", "driverfiles", "drivernodes", "resources"])
    def test_get_commands_with_execution_error(self, devcon, command):
        func_dict = {
            "hwids": devcon.get_hwids,
            "find": devcon.find_devices,
            "driverfiles": devcon.get_driverfiles,
            "drivernodes": devcon.get_drivernodes,
            "resources": devcon.get_resources,
        }
        devcon._connection.execute_command.side_effect = DevconExecutionError(
            returncode=1, cmd=f"C:\\devcon\\devcon_x64.exe {command} =usb"
        )
        with pytest.raises(DevconExecutionError):
            func_dict[command](pattern="=usb")

    @pytest.mark.parametrize("command", ["hwids", "find", "driverfiles", "drivernodes", "resources"])
    def test_get_commands_with_known_errors(self, devcon, command):
        output = dedent(
            """\
        No matching devices found.
            """
        )
        func_dict = {
            "hwids": devcon.get_hwids,
            "find": devcon.find_devices,
            "driverfiles": devcon.get_driverfiles,
            "drivernodes": devcon.get_drivernodes,
            "resources": devcon.get_resources,
        }
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=f"C:\\devcon\\devcon_x64.exe {command} "
            f'"@PCI\\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\\3&1C6B4348&0&6"',
            stdout=output,
            return_code=0,
            stderr="",
        )
        with pytest.raises(DevconException, match="No matching devices found"):
            func_dict[command](device_id="PCI\\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\\3&1C6B4348&0&6")

    def test_get_device_id(self, devcon):
        output = dedent(
            """\
        PCI\\VEN_8086&DEV_2F1F&SUBSYS_2F1F8086&REV_02\\3&103A9D54&0&87: Base System Device
        ACPI_HAL\\PNP0C08\\0                                          : Microsoft ACPI-Compliant System
        ROOT\\BASICRENDER\\0000                                       : Microsoft Basic Render Driver
        3 matching device(s) found.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert (
            devcon.get_device_id(device_name="Base System Device")
            == "PCI\\VEN_8086&DEV_2F1F&SUBSYS_2F1F8086&REV_02\\3&103A9D54&0&87"
        )
        assert devcon.get_device_id(device_name="Microsoft ACPI-Compliant System") == "ACPI_HAL\\PNP0C08\\0"

    def test_get_device_id_no_match(self, devcon):
        output = dedent(
            """\
        PCI\\VEN_8086&DEV_2F1F&SUBSYS_2F1F8086&REV_02\\3&103A9D54&0&87: Base System Device
        ACPI_HAL\\PNP0C08\\0                                          : Microsoft ACPI-Compliant System
        ROOT\\BASICRENDER\\0000                                       : Microsoft Basic Render Driver
        3 matching device(s) found.
            """
        )
        devcon._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert devcon.get_device_id(device_name="Microsoft ACPI-Compliant") is None

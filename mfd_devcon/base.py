# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Main devcon module."""

import logging

from pathlib import Path
from typing import Optional, Union, List
from mfd_common_libs import add_logging_level, log_levels, os_supported
from mfd_connect import Connection, LocalConnection
from mfd_connect.util import rpc_copy_utils
from mfd_base_tool import ToolTemplate
from mfd_typing import OSName, OSBitness
from .exceptions import DevconNotAvailable, DevconException, DevconExecutionError

from mfd_devcon import DevconParser, DevconHwids, DevconDriverNodes, DevconDriverFiles, DevconDevices, DevconResources

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class Devcon(ToolTemplate):
    """Class for Devcon."""

    tool_executable_name = {
        (OSName.WINDOWS, OSBitness.OS_32BIT): "devcon.exe",
        (OSName.WINDOWS, OSBitness.OS_64BIT): "devcon_x64.exe",
    }

    known_errors = ["Operation not permitted", "No matching devices found"]
    parser = DevconParser()

    @os_supported(OSName.WINDOWS)
    def __init__(self, connection: "Connection", absolute_path_to_binary_dir: str | Path = None):
        """Initialize Devcon."""
        self._connection = connection
        self.absolute_path_to_binary_dir = absolute_path_to_binary_dir
        if not self.absolute_path_to_binary_dir:
            self.absolute_path_to_binary_dir = self._connection.path("c:\\mfd_tools\\devcon\\")
        super().__init__(connection=connection, absolute_path_to_binary_dir=self.absolute_path_to_binary_dir)

    def _get_tool_exec_factory(self) -> str:
        """Get correct tool name."""
        return self.tool_executable_name[(self._connection.get_os_name(), self._connection.get_os_bitness())]

    def check_if_available(self) -> None:
        """
        Check if tool is available in system at the specified path.

        :raises DevconNotAvailable when tool not available
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Check if Devcon is available")
        self._connection.execute_command(
            f"{self._tool_exec} help", expected_return_codes=[0], custom_exception=DevconNotAvailable
        )

    def get_version(self) -> Optional[str]:
        """
        Get version of tool.

        :return: N/A since Devcon tool version is not available
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Tool version is not available for devcon")
        return "N/A"

    def enable_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Enable devices on the computer.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to be enabled specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon enable")
        command_list = [self._tool_exec, "enable"]
        if reboot:
            command_list.insert(1, "/r")
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Enabling devices using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return output.stdout

    def disable_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Disable devices on the computer.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to be disabled specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon disable")
        command_list = [self._tool_exec, "disable"]
        if reboot:
            command_list.insert(1, "/r")
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Disabling devices using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return output.stdout

    def rescan_devices(self) -> str:
        """
        Rescan to update the device list for the computer.

        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Rescan devices using command: devcon rescan")
        command = f"{self._tool_exec} rescan"
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return output.stdout

    def remove_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Remove the device from the device tree and deletes the device stack for the device.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get hwids for specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon remove")
        command_list = [self._tool_exec, "remove"]
        if reboot:
            command_list.insert(1, "/r")
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Removing devices using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return output.stdout

    def update_drivers(self, device_id: str, inf_file: Union["Path", str], reboot: bool = False) -> str:
        """
        Replace the current device drivers for a specified device with drivers listed in the specified INF file.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param inf_file: full path and file name of the INF (information) file used in the update
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        command_list = [self._tool_exec, "update", inf_file, f'"{device_id}"']
        if reboot:
            command_list.insert(1, "/r")
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Updating drivers using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return output.stdout

    def restart_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Stop and restart the specified devices.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get hwids for specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon restart")
        command_list = [self._tool_exec, "restart"]
        if reboot:
            command_list.insert(1, "/r")
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Restarting devices using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return output.stdout

    def get_hwids(self, device_id: str = "", pattern: str = "") -> List[DevconHwids]:
        """
        Display the hardware IDs, compatible IDs, and device instance IDs of the specified devices.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get hwids for specified by ID, class, or all devices (*)
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon hwids")
        command_list = [self._tool_exec, "hwids"]
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Get hwids using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return self.parser.parse_devcon_hwids(output.stdout)

    def get_drivernodes(self, device_id: str = "", pattern: str = "") -> List[DevconDriverNodes]:
        """
        Get all driver packages that are compatible with the device, along with their version and ranking.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get drivernodes for specified by ID, class, or all devices (*)
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon drivernodes")
        command_list = [self._tool_exec, "drivernodes"]
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Get drivernodes using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return self.parser.parse_devcon_drivernodes(output.stdout)

    def get_driverfiles(self, device_id: str = "", pattern: str = "") -> List[DevconDriverFiles]:
        """
        Get the full path and file name of installed INF files and device driver files for the specified devices.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get driverfiles for specified by ID, class, or all devices (*)
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon driverfiles")
        command_list = [self._tool_exec, "driverfiles"]
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Get driverfiles using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return self.parser.parse_devcon_driverfiles(output.stdout)

    def find_devices(self, device_id: str = "", pattern: str = "") -> List[DevconDevices]:
        """
        Find devices that are currently attached to the computer.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to look for specified by ID, class, or all devices (*)
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon find")
        command_list = [self._tool_exec, "find"]
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Find devices using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return self.parser.parse_devcon_devices(output.stdout)

    def listclass(self, class_name: str) -> List[DevconDevices]:
        """
        List all devices in the specified device setup classes.

        :param class_name: device setup class
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not class_name:
            raise AttributeError("Please provide value for class_name. Input: class_name cannot be empty")
        _specific_errors = [
            f'There is no "{class_name}" setup class',
            "No devices for setup class",
            "There are no devices in setup class",
        ]
        errors = self.known_errors + _specific_errors
        logger.log(
            level=log_levels.MODULE_DEBUG, msg=f"List all devices in the specified device setup class: {class_name}"
        )
        command_list = [self._tool_exec, "listclass", class_name]
        command = " ".join(command_list)
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        return self.parser.parse_devcon_devices(output.stdout, command="listclass")

    def get_resources(
        self, device_id: str = "", pattern: str = "", resource_filter: str = "all"
    ) -> List[DevconResources]:
        """
        Get the resources allocated to the specified devices.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get resources for specified by ID, class, or all devices (*)
        :param resource_filter: specify resources to be fetched for a given device.
                                return only specified resources if any
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        if not device_id and not pattern:
            raise AttributeError("Please provide inputs: device_id or pattern for command: devcon resources")
        command_list = [self._tool_exec, "resources"]
        if device_id:
            command_list.append(f'"@{device_id}"')
        else:
            command_list.append(f'"{pattern}"')
        command = " ".join(command_list)
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Get resources using command: {command}")
        output = self._connection.execute_command(command, custom_exception=DevconExecutionError, shell=True)
        for e in self.known_errors:
            if e in output.stdout:
                raise DevconException(f"Error while running devcon command: {e}")
        parsed_output = self.parser.parse_devcon_resources(output.stdout)
        if resource_filter != "all":
            for entry in range(len(parsed_output)):
                filtered_resources = []
                for resource in parsed_output[entry].resources:
                    if resource_filter.lower() in resource.lower():
                        filtered_resources.append(resource)
                parsed_output[entry].resources = filtered_resources
        return parsed_output

    def get_device_id(self, device_name: str, command: str = "find", class_name: str = "net") -> Union[str, None]:
        """
        Get the device instance ID from the specified device name.

        :param device_name: name of the requested device
        :param command: devcon command to execute for finding the device id
        :param class_name: device setup class of the specified device
        :return: device instance ID of the requested device
        """
        _valid_commands = ["find", "listclass"]
        if command not in _valid_commands:
            raise AttributeError(
                f"Invalid value = {command} for attribute: command. Valid commands are: {_valid_commands}"
            )
        if command == "find":
            devcon_devices = self.find_devices(pattern=f"={class_name}")
        else:
            devcon_devices = self.listclass(class_name=class_name)
        for device in devcon_devices:
            if device_name.strip() == device.device_desc:
                return device.device_instance_id
        return None

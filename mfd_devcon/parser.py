# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Main for Devcon parser."""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from mfd_common_libs import log_levels

from .exceptions import DevconParserException

logger = logging.getLogger(__name__)


@dataclass
class DevconHwids:
    """Structure for devcon hwids."""

    device_pnp: str
    name: str
    hardware_ids: List[str]
    compatible_ids: Optional[List[str]] = None


@dataclass
class DevconDriverNodes:
    """Structure for devcon drivernodes."""

    device_pnp: str
    name: str
    driver_nodes: Optional[dict] = None


@dataclass
class DevconDriverFiles:
    """Structure for devcon driverfiles."""

    device_pnp: str
    name: str
    installed_from: str
    driver_files: List[str]


@dataclass
class DevconDevices:
    """Structure for devcon find and devcon listclass."""

    device_instance_id: str
    device_desc: Optional[str] = ""


@dataclass
class DevconResources:
    """Structure for devcon resources."""

    device_pnp: str
    name: str
    resources: Optional[List[str]] = None


class DevconParser:
    """Class for parsing devcon command outputs."""

    def _fetch_hw_and_compatible_ids(self, output_per_device: str) -> Tuple[List[str], List[str]]:
        """
        Parse hardware and compatible ID's for each device.

        :param output_per_device: devcon output per device
        :return parsed hardware and compatible ids
        """
        hw_ids, compatible_ids = [], []
        ids_re = re.search(r".*(?P<hw_and_compatible>Hardware IDs:(?:\s+.+\s)+)", output_per_device)
        if ids_re:
            ids = ids_re.groupdict()["hw_and_compatible"]
            hw_ids_str, compatible_ids_str = ids, None
            if "Compatible IDs:" in ids:
                splits = ids.split("Compatible IDs:\n")
                hw_ids_str, compatible_ids_str = splits[0], splits[1]
            hwids_split = hw_ids_str.strip().split("\n")
            for entry in hwids_split:
                if hwids_split.index(entry) != 0:
                    hw_ids.append(entry.strip())
            if compatible_ids_str is not None:
                compatible_ids_split = compatible_ids_str.strip().split("\n")
                for entry in compatible_ids_split:
                    compatible_ids.append(entry.strip())
        return hw_ids, compatible_ids

    def parse_devcon_hwids(self, output: str) -> List[DevconHwids]:
        """
        Parse devcon output for command: devcon hwids.

        :param output: devcon command raw output
        :return: parsed devcon output containing data structure for each device
        :raises DevonParserException: if parser is unable to parse hardware and compatible ID's
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=output)
        num_devices_match = re.search(r"(?P<num_devices>[0-9]+) matching device\(s\) found", output)
        if not num_devices_match:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        num_devices = int(num_devices_match.groupdict()["num_devices"])
        output_per_device_split = re.split(r"^\S+\n", output, flags=re.M)
        output_per_device = list(filter(None, output_per_device_split))
        if len(output_per_device) != num_devices:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        devices = re.findall(r"^(\S+)\n", output, flags=re.M)
        if not devices:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        if len(list(devices)) != num_devices:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        devcon_hwids_op = []
        for device, output_per_device_value in zip(devices, output_per_device):
            pnp = device
            name = ""
            name_re = re.search(r"Name:\s(?P<name>.+)\n", output_per_device_value)
            if name_re:
                name = name_re.groupdict()["name"]
            hw_ids, compatible_ids = self._fetch_hw_and_compatible_ids(output_per_device_value)
            devcon_hwids_op.append(
                DevconHwids(device_pnp=pnp, name=name, hardware_ids=hw_ids, compatible_ids=compatible_ids)
            )
        return devcon_hwids_op

    def parse_devcon_drivernodes(self, output: str) -> List[DevconDriverNodes]:
        """
        Parse devcon output for command: devcon drivernodes.

        :param output: devcon command raw output
        :return: parsed devcon output containing data structure for each device
        :raises DevonParserException: if parser is unable to parse devcon output for drivernodes
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=output)
        num_devices_match = re.search(r"(?P<num_devices>[0-9]+) matching device\(s\) found", output)
        if not num_devices_match:
            raise DevconParserException("ERROR while parsing Devcon output for drivernodes")
        num_devices = int(num_devices_match.groupdict()["num_devices"])
        output_per_device_split = re.split(r"\S+\s+Name:\s.+\s+", output, flags=re.M)
        output_per_device = list(filter(None, output_per_device_split))
        if len(output_per_device) != num_devices:
            raise DevconParserException("ERROR while parsing Devcon output for drivernodes")
        devices = re.findall(r"^(\S+)\s+Name:\s+(.+)\n", output, flags=re.M)
        if not devices:
            raise DevconParserException("ERROR while parsing Devcon output for drivernodes")
        if len(list(devices)) != num_devices:
            raise DevconParserException("ERROR while parsing Devcon output for drivernodes")
        device_drivernodes = []
        for device, output_per_device_value in zip(devices, output_per_device):
            pnp = device[0]
            name = device[1]
            drivernodes_search = re.finditer(
                r"Driver node #(?P<num>[0-9]+):\s+Inf file is\s+(?P<inf_file>.+)\s+Inf section is\s+(?P<inf_section>.+)"
                r"\s+Driver description is\s+(?P<driver_desc>.+)\s+Manufacturer name is\s+(?P<manufacturer_name>.+)\s+"
                r"Provider name is\s+(?P<provider_name>.+)\s+Driver date is\s+(?P<driver_date>.+)\s+Driver version "
                r"is\s+(?P<driver_version>.+)\s+Driver node rank is\s+(?P<driver_node_rank>.+)\s+Driver node "
                r"flags are\s+(?P<driver_node_flags>.+)\s",
                output_per_device_value,
            )
            drivernodes = {}
            for driver_node in drivernodes_search:
                node_details = {}
                node_num = driver_node.groupdict()["num"]
                node_details["inf_file"] = driver_node.groupdict()["inf_file"]
                node_details["inf_section"] = driver_node.groupdict()["inf_section"]
                node_details["driver_desc"] = driver_node.groupdict()["driver_desc"]
                node_details["manufacturer_name"] = driver_node.groupdict()["manufacturer_name"]
                node_details["provider_name"] = driver_node.groupdict()["provider_name"]
                node_details["driver_date"] = driver_node.groupdict()["driver_date"]
                node_details["driver_version"] = driver_node.groupdict()["driver_version"]
                node_details["driver_node_rank"] = driver_node.groupdict()["driver_node_rank"]
                node_details["driver_node_flags"] = driver_node.groupdict()["driver_node_flags"]
                drivernodes[node_num] = node_details
            device_drivernodes.append(DevconDriverNodes(device_pnp=pnp, name=name, driver_nodes=drivernodes))
        return device_drivernodes

    def parse_devcon_driverfiles(self, output: str) -> List[DevconDriverFiles]:
        """
        Parse devcon output for command: devcon driverfiles.

        :param output: devcon command output
        :return: parsed devcon output containing data structure for each device
        :raises DevonParserException: if parser is unable to parse devcon output for driverfiles
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=output)
        num_devices_match = re.search(r"(?P<num_devices>[0-9]+) matching device\(s\) found", output)
        if not num_devices_match:
            raise DevconParserException("ERROR while parsing Devcon output for driverfiles")
        num_devices = int(num_devices_match.groupdict()["num_devices"])
        search_string = (
            r"(\S+)\n\s+Name:\s+(.+)\s+Driver installed from (.+)\.\s[0-9]+\sfile\(s\) used by "
            r"driver:\n((\s+\S+\n*)+)"
        )
        search_op = re.findall(search_string, output, flags=re.M)
        search_string_no_driverfiles = (
            r"(\S+)\n\s+Name:\s+(.+)\s+Driver installed from (.+)\.\sThe driver is not using any files."
        )
        search_op_no_driverfiles = re.findall(search_string_no_driverfiles, output, flags=re.M)
        search_output = search_op + search_op_no_driverfiles
        if len(search_output) != num_devices:
            raise DevconParserException("Could not parse Devcon driverfiles output for all devices")
        driverfiles = []
        for entry in search_output:
            driver_files = []
            pnp = entry[0]
            name = entry[1]
            installed_from = entry[2]
            if len(entry) == 5:
                files = entry[3]
                split_files = files.split()
                for file in split_files:
                    driver_files.append(file.strip())
            driverfiles.append(
                DevconDriverFiles(device_pnp=pnp, name=name, installed_from=installed_from, driver_files=driver_files)
            )
        return driverfiles

    def parse_devcon_devices(self, output: str, command: str = "find") -> List[DevconDevices]:
        """
        Parse devcon output for command: devcon find/ devcon listclass.

        :param output: devcon command output
        :param command: devcon command executed for which output is to be parsed. example: find, listclass
        :return: parsed devcon output containing data structure for each device
        :raises DevonParserException: if parser is unable to parse devcon output for specified devcon command
        """
        _valid_commands = ["find", "listclass"]
        if command not in _valid_commands:
            raise AttributeError(f"Invalid command: {command}. Valid commands: {_valid_commands}")
        if command == "listclass":
            num_devices_match = re.search(r"Listing (?P<num_devices>[0-9]+) devices in setup class", output)
        else:
            num_devices_match = re.search(r"(?P<num_devices>[0-9]+) matching device\(s\) found", output)
        if not num_devices_match:
            raise DevconParserException("ERROR while parsing Devcon output for find device")
        num_devices = int(num_devices_match.groupdict()["num_devices"])
        devices = []
        for device in output.split("\n"):
            if "matching device(s) found" in device or "Listing" in device or not device:
                continue
            if ":" in device:
                dev_splits = device.split(":")
                device_id = dev_splits[0].strip()
                device_desc = dev_splits[1].strip()
            else:
                device_id = device.strip()
                device_desc = ""
            devices.append(DevconDevices(device_instance_id=device_id, device_desc=device_desc))
        if num_devices != len(devices):
            raise DevconParserException("Could not parse Devcon output for all devices")
        return devices

    def parse_devcon_resources(self, output: str) -> List[DevconResources]:
        """
        Parse devcon output for command: devcon resources.

        :param output: devcon command output
        :return: parsed devcon output containing data structure for each device
        :raises DevonParserException: if parser is unable to parse devcon output for resources
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=output)
        num_devices_match = re.search(r"(?P<num_devices>[0-9]+) matching device\(s\) found", output)
        if not num_devices_match:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        num_devices = int(num_devices_match.groupdict()["num_devices"])
        output_per_device_split = re.split(r"^\S+\n", output, flags=re.M)
        output_per_device = list(filter(None, output_per_device_split))
        if len(output_per_device) != num_devices:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        devices = re.findall(r"^(\S+)\n", output, flags=re.M)
        if not devices:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        if len(list(devices)) != num_devices:
            raise DevconParserException("ERROR while parsing Devcon output for resources")
        devcon_resources = []
        for device, output_per_device_value in zip(devices, output_per_device):
            resources = []
            pnp = device
            name_re = re.search(r"Name:\s(.+)\n", output_per_device_value)
            if name_re:
                name = name_re.group(1)
            else:
                name = ""
            resources_search = re.search(
                r"Device is currently using the following resources:\n(?P<resources>(\s+.+\n*)+)",
                output_per_device_value,
            )
            if resources_search:
                resource_str = resources_search.groupdict()["resources"]
                resource_splits = filter(None, resource_str.split("\n"))
                for resource in resource_splits:
                    resources.append(resource.strip())
            devcon_resources.append(DevconResources(device_pnp=pnp, name=name, resources=resources))
        return devcon_resources

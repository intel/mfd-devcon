# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Simple example of usage."""

from mfd_connect import RPyCConnection
from mfd_devcon import Devcon

conn = RPyCConnection(ip="x.x.x.x")
devcon_obj = Devcon(connection=conn, absolute_path_to_binary_dir=r"C:\tools\devcon")
enable_dev = devcon_obj.enable_devices(
    device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63", reboot=True
)
print(enable_dev)
enable_dev_with_pattern = devcon_obj.enable_devices(pattern="pci*", reboot=True)
print(enable_dev_with_pattern)
disable_dev = devcon_obj.disable_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63")
print(disable_dev)
rescan_dev = devcon_obj.rescan_devices()
print(rescan_dev)
remove_dev = devcon_obj.remove_devices(pattern="=usb", reboot=True)
print(remove_dev)
update_drivers = devcon_obj.update_drivers(
    device_id=r"PCI\VEN_14E4&DEV_165F&SUBSYS_1F5B1028&REV_00\0000B82A72DA80E200",
    inf_file=r"C:\windows\inf\test.inf",
    reboot=True,
)
print(update_drivers)
restart_dev = devcon_obj.restart_devices(
    device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63", reboot=True
)
print(restart_dev)
get_hwids = devcon_obj.get_hwids(pattern="=net")
for device_hwid in get_hwids:
    print(device_hwid.device_pnp, device_hwid.name, device_hwid.hardware_ids, device_hwid.compatible_ids)
get_drivernodes = devcon_obj.get_drivernodes(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63")
print(get_drivernodes[0].device_pnp, get_drivernodes[0].name, get_drivernodes[0].driver_nodes)
driverfiles_get = devcon_obj.get_driverfiles(pattern="pci*")
for device_drivefile in driverfiles_get:
    print(
        device_drivefile.device_pnp,
        device_drivefile.name,
        device_drivefile.installed_from,
        device_drivefile.driver_files,
    )
find_devices = devcon_obj.find_devices(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63")
print(find_devices[0].device_instance_id, find_devices[0].device_desc)
listclass_dev = devcon_obj.listclass(class_name="net")
for device in listclass_dev:
    print(device.device_instance_id, device.device_desc)
get_resources = devcon_obj.get_resources(device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63")
print(get_resources[0].device_pnp, get_resources[0].name, get_resources[0].resources)
get_filtered_resources = devcon_obj.get_resources(
    device_id=r"PCI\VEN_8086&DEV_2FE3&SUBSYS_2FE38086&REV_02\3&1C6B4348&0&63", resource_filter="irq"
)
print(get_filtered_resources[0].device_pnp, get_filtered_resources[0].name, get_filtered_resources[0].resources)
device_id = devcon_obj.get_device_id(device_name="Microsoft ACPI-Compliant")
print(device_id)

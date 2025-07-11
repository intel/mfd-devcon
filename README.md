> [!IMPORTANT] 
> This project is under development. All source code and features on the main branch are for the purpose of testing or evaluation and not production ready.

> [!IMPORTANT]
> Starting from version v2.0.0, the `devcon.exe` and `devcon_x64.exe` binaries are no longer included in the repository. 
> You can download the latest version of Devcon from the [Windows driver samples](https://github.com/Microsoft/Windows-driver-samples) repository.
> 
> Remember to place them in the default location: `C:\mfd_tools\devcon\`

# MFD Devcon

A Python module that provides a programmatic interface to Windows Device Console (DevCon) tool commands. It implements the [mfd-base-tool](https://github.com/intel/mfd-tool) abstract class.

More about DevCon:
* https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/devcon
* https://github.com/microsoft/Windows-driver-samples/blob/main/setup/devcon/README.md

## Implemented methods
`check_if_available() -> None:` - Check if Devcon is available in system at the specified path, raises `DevconNotAvailable` if not

`get_version() -> str:` - Return N/A for Devcon as version is not available

`enable_devices(device_id: str = "", pattern: str = "", reboot: bool = False) -> str:` - Enable device(s) on the computer specified either by device_id or pattern. Set reboot to True for executing command with conditional reboot

`disable_devices(device_id: str = "", pattern: str = "", reboot: bool = False) -> str:` - Disable device(s) on the computer specified either by device_id or pattern. Set reboot to True for executing command with conditional reboot

`rescan_devices() -> str:` - Rescan to update the device list for the computer

`remove_devices(device_id: str = "", pattern: str = "", reboot: bool = False) -> str:` - Remove device(s) on the computer specified either by device_id or pattern. Set reboot to True for executing command with conditional reboot

`update_drivers(device_id: str, inf_file: Union[Path, str], reboot: bool = False) -> str:` - Replace the current device drivers for a device with drivers listed in the INF file

`restart_devices(device_id: str = "", pattern: str = "", reboot: bool = False) -> str:` - Restart device(s) on the computer specified either by device_id or pattern. Set reboot to True for executing command with conditional reboot

`get_hwids(device_id: str = "", pattern: str = "") -> List[DevconHwids]:` -  Displays the hardware IDs, compatible IDs, and device instance IDs of the specified devices

`get_drivernodes(device_id: str = "", pattern: str = "") -> List[DevconDriverNodes]:` -  Get all driver packages compatible with the device, with version and ranking

`get_driverfiles(device_id: str = "", pattern: str = "") -> List[DevconDriverFiles]:` - Get full path and file name of installed INF files and device driver files for the specified devices

`find_devices(device_id: str = "", pattern: str = "") -> List[DevconDevices]:` - List device information for specified devices

`listclass(class_name: str) -> List[DevconDevices]:` -  Lists all devices in the specified device setup classes

`get_resources(device_id: str = "", pattern: str = "", resource_filter: str = "all") -> List[DevconResources]:` - Get the resources allocated to the specified devices

`get_device_id(device_name: str, command: str = "find", class_name: str = "net") -> Union[str, None]:` - Get the device instance ID from the specified device name
        

## Data structures
Data structures returned by methods:
```python
class DevconHwids:
    """Structure for devcon hwids."""

    device_pnp: str
    name: str
    hardware_ids: List[str]
    compatible_ids: Optional[List[str]] = None

class DevconDriverNodes:
    """Structure for devcon drivernodes."""

    device_pnp: str
    name: str
    driver_nodes: Optional[dict] = None

class DevconDriverFiles:
    """Structure for devcon driverfiles."""

    device_pnp: str
    name: str
    installed_from: str
    driver_files: List[str]

class DevconDevices:
    """Structure for devcon find and devcon listclass."""

    device_instance_id: str
    device_desc: Optional[str] = ""

class DevconResources:
    """Structure for devcon resources."""

    device_pnp: str
    name: str
    resources: Optional[List[str]] = None
```

## OS supported:

* WINDOWS

## Issue reporting

If you encounter any bugs or have suggestions for improvements, you're welcome to contribute directly or open an issue [here](https://github.com/intel/mfd-devcon/issues).

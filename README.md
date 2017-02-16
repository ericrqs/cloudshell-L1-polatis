# cloudshell-L1-Polatis

## Installation
Copy to c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers on CloudShell machine:
- PolatisDriver.exe (If the EXE was downloaded directly from the web, be sure to right click the EXE, open Properties, and *UNBLOCK* the file)
- polatis_runtime_configuration.json

To customize the port, prompts, and other driver-specific settings, edit:
- polatis_runtime_configuration.json

Import polatis_datamodel.xml into Resource Manager

## Usage
- Import polatis_datamodel.xml into Resource Manager
- Create L1 switch resource and set IP address, username, password
- In Configuration view in Resource Manager, push Auto Load
- Create multiple DUTs each with a port subresource
- In Connections view of the L1 switch resource, connect the DUT ports
- Create an empty reservation and add DUTs
- Create a route between two DUTs
- Connect the route
- See log files in c:\Program Files (x86)\QualiSystems\CloudShell\Server\Logs\\Polatis_*\

Check for error messages in:
- c:\\Program Files (x86)\\QualiSystems\\CloudShell\\Server\\Logs\\Polatis
- c:\\Program Files (x86)\\QualiSystems\\CloudShell\\Server\\Logs\\TeamServer.Service.txt.


## Development

### Prerequisites
- Python must be in PATH
- PyInstaller must be installed
  - http://www.pyinstaller.org/
  - Download and extract the zip
  - python setup.py install
- git must be installed
  - https://git-scm.com/
  - Enable Git Bash if asked
- In Git Bash:
  - git clone https://github.com/QualiSystems/cloudshell-L1-Polatis.git


### What to edit
- polatis_l1_handler.py
  - Fill in the implementation for any relevant L1 driver functions: login, logout, get_resource_details, map_bidi, map_uni, map_clear, map_clear_to, get_attribute_value, get_state_id, set_state_id
  - Load all settings from c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers\\polatis_runtime_configuration.json
  - Handle all communication with the device
    - e.g. paramiko
    - e.g. requests
- polatis_datamodel.xml
  - Optionally customize the family or model names for the switch, blade, and port resources 
- polatis_runtime_configuration.json
  - Set default values to be shipped in the default JSON file
  - Define new custom driver settings
  - See notes below

### compile_driver.bat
- Run from a cmd command prompt &mdash; *NOTE: MUST BE RUNNING AS ADMINISTRATOR*
- Kills all PolatisDriver.exe
- Copies files to c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers:
  - .\dist\\PolatisDriver.exe
  - .\\polatis_runtime_configuration.json
- Copies files to release/ folder:
  - .\dist\\PolatisDriver.exe
  - .\\polatis_runtime_configuration.json
  - .\\polatis_datamodel.xml

### Notes

You should not need to edit main.py, l1_driver.py, l1_driver_resource_info.py, or l1_handler_base.py.

Edit the driver logic in polatis_l1_handler.py.

polatis_l1_handler.py manages the lifetime of the device connection.

Implementations are provided for typical TL1 and SSH/Telnet ("CLI", via cloudshell-cli package).

Sample code for TL1 and CLI are ready to uncomment in polatis_l1_handler.py.

If the device uses TL1, customize polatis_tl1_connection.py if the device differs from the expected defaults.

If the device uses a CLI, try to customize polatis_cli_connection.py based on the sample commands and modes. The modes (default, enable, configure) are based on a typical Cisco switch. The sample "show interfaces" is set up to automatically answer a typical --More-- prompt. The cloudshell-cli package has many areas for customization. Alternatively you can bypass cloudshell-cli and polatis_cli_connection.py entirely and connect directly to the device using Paramiko.

For REST APIs, try the "requests" package. Note that even if your device has no notion of a persistent connection, you still need to implement login() and store the address, username, and password, since they are passed to login() and not the mapping functions.

Any additional dependencies you add must be installed on the Python in PATH. PyInstaller will automatically bundle all these dependencies into the EXE.

If the driver doesn't work, try running the EXE from the command line with no arguments. It should print "Dependency check OK - exiting". Problems with dependencies may print a stack trace.

The address, username, and password of the switch resource become known to the driver only when 'login' is called. 

The port number is not stored on the resource. If it can't just be hard coded in the driver, take the setting from c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers\\polatis_runtime_configuration.json.

### JSON config
The sample code includes hard-coding of default values for the JSON settings. In the sample, it is reread every time login() is called.

CLI prompts on some switches can be completely arbitrary. A JSON setting is included for customizing the prompt regex. This is to avoid having to recompile the driver in the event that the customer switch has been given a bizarre prompt. If you don't have such prompt issues, you can delete all code related to this setting.

polatis_runtime_configuration.json is not mandatory. If your driver doesn't need any runtime settings, you can delete all the code in polatis_l1_handler.py that deals with the JSON.


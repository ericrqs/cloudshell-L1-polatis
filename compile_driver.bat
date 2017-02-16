@echo off
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ok
) else (
    echo This program must be run from an administrator cmd prompt
    goto :fail
)

@echo on

pip install cloudshell-core cloudshell-cli

pyinstaller --onefile driver.spec

taskkill /f /im PolatisDriver.exe

timeout 3

set driverdir="c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers"
IF EXIST %driverdir% GOTO :havecs
set driverdir="c:\Program Files (x86)\QualiSystems\TestShell\Server\Drivers"
:havecs


copy dist\PolatisDriver.exe  %driverdir%
copy polatis_runtime_configuration.json %driverdir%



copy polatis_datamodel.xml               release\
copy dist\PolatisDriver.exe        release\
copy polatis_runtime_configuration.json  release\

:fail

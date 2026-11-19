@echo off
setlocal
cd /d "%~dp0"
if not exist "teleportation_model.py" goto missing
python -c "import tkinter; import sys; assert sys.version_info.major == 3" >nul 2>nul
if not errorlevel 1 goto usepython
py -3 -c "import tkinter" >nul 2>nul
if not errorlevel 1 goto usepy
for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
  if exist "%%~fD\python.exe" (
    "%%~fD\python.exe" -c "import tkinter" >nul 2>nul
    if not errorlevel 1 (
      set "TELEPORT_PYTHON=%%~fD\python.exe"
      goto uselocal
    )
  )
)
echo Python 3 with Tkinter could not be found.
echo Install standard Python 3 for Windows from https://www.python.org/downloads/
echo Include Tcl/Tk and add Python to PATH during installation.
pause
exit /b 1

:usepython
python "teleportation_model.py" 2>"launch_error.log"
goto finished
:usepy
py -3 "teleportation_model.py" 2>"launch_error.log"
goto finished
:uselocal
"%TELEPORT_PYTHON%" "teleportation_model.py" 2>"launch_error.log"
goto finished
:finished
if not errorlevel 1 exit /b 0
echo The model could not run. Error details:
type "launch_error.log"
echo Please share the launch_error.log file if you need help.
pause
exit /b 1
:missing
echo Extract the entire ZIP first, then run Launch_Model.cmd inside the extracted folder.
echo The file teleportation_model.py must be beside this launcher.
pause
exit /b 1

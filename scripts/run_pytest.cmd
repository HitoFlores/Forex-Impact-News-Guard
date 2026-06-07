@echo off
setlocal
set "TEMP=.tmp"
set "TMP=.tmp"
set "TMPDIR=.tmp"
if not exist ".tmp" mkdir ".tmp"
".venv\Scripts\python.exe" -m pytest -q
endlocal

@echo off
setlocal

cd %~dp0\..

set PYTHONPATH=%CD%

coverage run -m unittest discover
::coverage run -m run_tests
coverage html

endlocal
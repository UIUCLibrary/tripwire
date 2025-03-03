@echo off
py -m venv venv
venv\Scripts\pip install --disable-pip-version-check uv

REM Generates the .egg-info needed for the version metadata
venv\Scripts\uv build --wheel

venv\Scripts\uv run --with-requirements requirements.txt contrib/create_standalone.py tripwire  ./uiucprescon/tripwire/__main__.py

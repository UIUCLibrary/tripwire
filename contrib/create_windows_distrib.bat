@echo off
py -m venv venv
venv\Scripts\pip install --disable-pip-version-check uv

REM Generates the .egg-info needed for the version metadata
venv\Scripts\uv build --wheel

venv\Scripts\uv run contrib/create_standalone.py avtool  ./avtool/__main__.py

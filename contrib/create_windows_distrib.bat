@echo off
py -m venv venv
venv\Scripts\pip install --disable-pip-version-check uv

REM Generates the .egg-info needed for the version metadata
venv\Scripts\uv build --wheel
venv\Scripts\uv export --format requirements-txt --no-dev --no-emit-project > %TEMP%\requirements.txt
venv\Scripts\uv run --with-requirements %TEMP%\requirements.txt contrib/create_standalone.py --include-tab-completions tripwire  contrib/bootstrap_standalone.py

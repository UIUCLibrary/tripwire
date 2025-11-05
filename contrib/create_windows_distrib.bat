@echo off
py -m venv venv
venv\Scripts\pip install --disable-pip-version-check uv

REM Generates the .egg-info needed for the version metadata
venv\Scripts\uv build --python 3.13 --wheel
venv\Scripts\uv export --python 3.13 --format requirements-txt --no-dev --no-emit-project > %TEMP%\requirements.txt
venv\Scripts\uv run --python 3.13 --with-requirements %TEMP%\requirements.txt contrib/create_standalone.py --include-tab-completions tripwire  contrib/bootstrap_standalone.py

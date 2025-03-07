#!/usr/bin/env bash

set -e

FREEZE_SCRIPT=$(dirname "$0")/create_standalone.py

DEFAULT_BUILD_VENV=$(mktemp -d)

default_python_path=$(which python3)


create_standalone(){
    uv_path=$1
    echo 'create_standalone'
    shift;

#     Generates the .egg-info needed for the version metadata
    $uv_path build --wheel

    $uv_path run --with-requirements requirements.txt $FREEZE_SCRIPT --include-tab-completions tripwire ./uiucprescon/tripwire/__main__.py
}


create_venv() {
    base_python_path=$1
    venv_path=$2
    $base_python_path -m venv $venv_path
    . $venv_path/bin/activate
    python -m pip install --disable-pip-version-check uv
    deactivate
}

if ! command -v uv 2>&1 >/dev/null
then
    build_venv=$DEFAULT_BUILD_VENV
    python_path=$default_python_path

    create_venv $python_path $build_venv
    trap "rm -rf $build_venv" EXIT
    uv_exec="$build_venv/bin/uv"
else
    uv_exec=$(which uv)
fi

create_standalone $uv_exec

#!/usr/bin/env bash

set -e

FREEZE_SCRIPT=$(dirname "$0")/create_standalone.py

DEFAULT_PYTHON_VERSION='3.14+GIL'
DEFAULT_BUILD_VENV=$(mktemp -d)

default_python_path=$(which python3)

create_standalone(){
    local wheel
    local uv_path
    local python_version

    uv_path=$1
    wheel=$2
    python_version=$3
    echo 'create_standalone'
    shift;

#     Generates the .egg-info needed for the version metadata
    temp_dir=$(mktemp -d)
    $uv_path build --python="$python_version" --wheel
    $uv_path export --python="$python_version" --frozen --no-dev --no-emit-project --no-annotate --group standalone-packaging --extra gui --format pylock.toml --output-file "${temp_dir}/pylock.gui.toml" > /dev/null
    $uv_path run --python="$python_version" "$FREEZE_SCRIPT" --package-manager=uv --include-tab-completions --requirements "${temp_dir}/pylock.gui.toml" --cli-entrypoint=./contrib/bootstrap_standalone_cli.py --gui-entrypoint=./contrib/bootstrap_standalone_gui.py "${wheel}" tripwire
}

print_usage(){
    echo "Usage: $0 [options] wheel"
}

show_help() {
    print_usage
    echo
    echo "Arguments:"
    echo "  wheel            Python (.whl) Wheel file  to use. "
    echo
    echo "Options:"
    echo "  --python-version=VERSION Python version to use (default: 3.12+gil)"
    echo "  --help           Display this help message and exit."
}


create_venv() {
    base_python_path=$1
    venv_path=$2
    $base_python_path -m venv $venv_path
    . $venv_path/bin/activate
    python -m pip install --disable-pip-version-check uv
    deactivate
}

python_version="$DEFAULT_PYTHON_VERSION"

while [[ $# -gt 0 ]]; do
  case $1 in
    --python-version=*)
      python_version="${1#*=}"
      shift
      ;;
    --python-version)
      python_version="$2"
      shift 2
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      print_usage
      exit 1
      ;;
    *)
      wheel="$1"
      shift
      break
      ;;
  esac
done

if [ -z "$wheel" ]; then
  echo "Error: Missing wheel argument."
  print_usage
  exit 1
fi

if ! command -v uv 2>&1 >/dev/null
then
    build_venv=$DEFAULT_BUILD_VENV
    python_path=$default_python_path

    create_venv "$python_path" "$build_venv"
    trap 'rm -rf "$build_venv"' EXIT
    uv_exec="$build_venv/bin/uv"
else
    uv_exec=$(which uv)
fi

create_standalone "$uv_exec" "$wheel" "$python_version"

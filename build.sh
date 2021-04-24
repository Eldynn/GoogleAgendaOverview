#!/usr/bin/env bash

BASEDIR=$(dirname "$0")

pyinstaller --onefile --windowed --icon="${BASEDIR}/main.ico" "${BASEDIR}/main.py"
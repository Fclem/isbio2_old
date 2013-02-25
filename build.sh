#!/bin/bash

echo $0: Creating Virtual Environment
virtualenv --prompt="<venv>" ./venv

mkdir ./logs
mkdir ./pids

echo $0: Installing Dependencies
source ./venv/bin/activate
export PIP_REQUIRE_VIRTUALENV=true
./venv/bin/pip install --requirement=./requirements.txt --log=./logs/build_pip_packages.log

echo $0: !BUILD FINISHED!

#!/bin/bash

echo $0: Creating Virtual Environment
virtualenv --prompt="<venv>" ./venv

mkdir ./logs
mkdir ./pids
mkdir ./static
mkdir ./db
mkdir ./tmp

echo $0: Installing Dependencies
source ./venv/bin/activate
export PIP_REQUIRE_VIRTUALENV=true
./venv/bin/pip install --requirement=./requirements.txt --log=./logs/build_pip_packages.log

echo $0: Collect Static Files
python isbio/manage.py collectstatic

echo $0: !BUILD FINISHED!

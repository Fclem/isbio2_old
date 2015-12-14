#!/bin/bash

Red='\033[0;31m'          # Red
Color_Off='\033[0m'       # Text Reset

source ./venv/bin/activate
killall python > /dev/null
printf "${Red}STARTING BREEZE...${Color_Off}\n"
python ./isbio/manage.py runserver
printf "${Red}BREEZE WAS TERMINATED, RE-LAUNCHING${Color_Off}\n"
./autorun.sh &

#perl /projects/fhrb_pm/bin/start-jdbc-bridge
# python ./isbio/manage.py run_gunicorn --bind=localhost:8000 --workers=5 --pid=./pids/gunicorn.pid --log-file ./logs/gunicorn.log

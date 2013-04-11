#!/bin/bash

source /homes/dbychkov/dev/isbio/venv/bin/activate
python /homes/dbychkov/dev/isbio/isbio/manage.py runserver
# python /home/dbychkov/dev/isbio/isbio/manage.py run_gunicorn --bind=localhost:8000 --workers=5 --pid=/home/dbychkov/dev/isbio/pids/gunicorn.pid --log-file /home/dbychkov/dev/isbio/logs/gunicorn.log

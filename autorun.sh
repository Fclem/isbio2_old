#!/bin/bash

echo "terminating any previously running autorun.sh..."
killall autorun_sub.sh > /dev/null 2>&1
killall re_run.sh > /dev/null 2>&1
./autorun_sub.sh &


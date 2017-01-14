#!/bin/bash

function daily {
        logger CRON DAILY
        #/usr/local/bin/quickreboot.sh &
}

function hourly {
        logger CRON HOURLY
        wget www.demo.io/device_ping /dev/null
        #sudo pull_git.sh
        #/usr/sbin/ntpdate -b cz.pool.ntp.org &> /dev/null &

function every_minute {
        logger CRON EVERY MINUTE
        sudo pull_git.sh
        echo "1 minute tasks from fake cron!"
        #TODO: Check if python App is running. 3 consecutive failure require Raspberry to re-start
}

#-----------------

num=1

while true; do

sleep 60

every_minute

if ! ((num % 1440)); then
        daily
elif ! ((num % 60)); then
        hourly
fi

num=$((num + 1))

done
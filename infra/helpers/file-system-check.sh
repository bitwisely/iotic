#!/bin/bash

# Run script as root
if [ $(id -u) != "0" ]
    then
        sudo "$0" "$@"
        exit $?
fi

strace -f -e trace=file `ps aux | tail -n +2 | awk '{ORS=" "; print $2}' | sed -e 's/\([0-9]*\)/\-p \1 /g' | sed -e 's/\-p  $//g'`

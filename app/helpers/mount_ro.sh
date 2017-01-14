#!/bin/bash

# check if any process is preventing ro mode change
# http://raspberrypi.stackexchange.com/questions/9813/raspbian-mount-is-busy-tried-to-remount-sd-card-as-read-only
lsof +L1; lsof|sed -n '/SYSV/d; /DEL\|(path /p;' |grep -Ev '/(dev|home|tmp|var)'

# sync file system
sync

# switch to read-only
mount -o remount,ro /
mount -o remount,ro /boot

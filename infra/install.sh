#!/bin/bash
# http://k3a.me/how-to-make-raspberrypi-truly-read-only-reliable-and-trouble-free/

echo "INSTALLING MODULES"
./apt_get_modules.sh

echo "CONFIGURING MODULES"
./configure_modules.sh

echo "INSTALLATION COMPLETED"
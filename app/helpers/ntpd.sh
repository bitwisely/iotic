#!/bin/bash

# Kill all ntpd running
killall -9 ntpd
# Update time with big jump and quit
ntpd -qg
# Start ntpd diamond
/etc/init.d/ntp start

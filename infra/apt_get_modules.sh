#!/bin/bash

# Run script as root
if [ $(id -u) != "0" ]
    then
        sudo "$0" "$@"
        exit $?
fi

######## PRE-START SETUP ##########

# Stop watchdog before update
/etc/init.d/watchdog stop

# Enable rw file system
../app/helpers/mount_rw.sh

# Sdcard life time extend hacks
# http://raspberrypi.stackexchange.com/questions/169/how-can-i-extend-the-life-of-my-sd-card

# Shutdown swap
swapoff --all

####### INSTALL MODULES #########

# Update system
apt-get update

# Remove swap support forever
apt-get -q -y remove dphys-swapfile

# Install python packages
pushd .
curl -OL https://github.com/kennethreitz/requests/tarball/master
tar -xf master
cd kennethreitz-requests-*/
python2 setup.py install
popd
rm -Rf kennethreitz-requests-*

# Remove unneccssary packagess
apt-get remove -y --purge wolfram-engine cron anacron logrotate dbus fake-hwclock dphys-swapfile xserver-common lightdm
insserv -r x11-common
apt-get autoremove -y --purge

insserv -r bootlogs
insserv -r alsa-utils # if you don't need alsa stuff (sound output)
insserv -r console-setup
insserv -r fake-hwclock # probably already removed at this point..

# Start installing required packages
apt-get install -y gpsd gpsd-clients python-gps # For GPS
apt-get install -y libreadline-dev # For thingmagic builds
apt-get install -y sqlite3 # Sqlite install
apt-get install libav-tools

apt-get install -y busybox-syslogd
dpkg --purge rsyslog

apt-get install -y python-pip
pip install docopt  # Option generator for helper python files

# Debug goodies
apt-get install -y lsof

######## POST-STOP SETUP ########

# Switch back to read only file system and enable watchdog
apt-get install -y watchdog
insserv watchdog
../app/helpers/mount_ro.sh
/etc/init.d/watchdog start
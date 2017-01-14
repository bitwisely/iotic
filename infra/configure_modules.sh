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


####### CONFIGURE MODULES #########

rm -rf /var/lib/dhcp/
ln -svf /tmp /var/lib/dhcp
rm -rf /var/run /var/spool /var/lock
ln -svf /tmp /var/run
ln -svf /tmp /var/spool
ln -svf /tmp /var/lock


# FSTAB and cmdline is node handled as partition can change wildly between installation to installation
# CONFIGURE THEM MANUALLY
# cp -vf ./confs/fstab /etc
# cp -vf ./confs/cmdline.txt /boot
#chown root:root /etc/fstab
#chmod 644 /etc/fstab
#chown root:root /boot/cmdline.txt
#chmod 755 /boot/cmdline.txt

# Add mount path for log sqlitedb mount path
mkdir -p /media/usbDISK

# File based configuration changes start:

# Folder for initial files before update
mkdir -p ../original_confs

cp -n /etc/inittab ../original_confs/ # Don't overwrite if file exists with -n
python2 ./helpers/auto_replace.py --file=/etc/inittab \
       --search="T0:23:respawn:/sbin/getty ­L ttyAMA0" \
       --replace="#T0:23:respawn:/sbin/getty ­L ttyAMA0"

# Configure DNS with google servers
cp -n /etc/network/interfaces ../original_confs/ # Don't overwrite if file exists with -n
cp -vf ./confs/interfaces /etc/network
chown root:root /etc/network/interfaces
chmod 644 /etc/network/interfaces

cp -n /etc/resolv.conf.head ../original_confs/ # Don't overwrite if file exists with -n
cp -vf ./confs/resolv.conf.head /etc
chown root:root /etc/resolv.conf.head
chmod 644 /etc/resolv.conf.head


cp -n /etc/watchdog.conf ../original_confs/ # Don't overwrite if file exists with -n
python2 ./helpers/auto_replace.py --file=/etc/watchdog.conf \
       --search="#watchdog-device" \
       --replace="watchdog-device"

python2 ./helpers/auto_replace.py --file=/etc/watchdog.conf \
       --search="#max-load-1" \
       --replace="max-load-1"

cp -n /etc/modules ../original_confs/ # Don't overwrite if file exists with -n
python2 ./helpers/search_append.py --file=/etc/modules \
       --key="bcm2708_wdog"

cp -n /etc/sysctl.conf ../original_confs/ # Don't overwrite if file exists with -n
python2 ./helpers/conf_append.py --file /etc/sysctl.conf \
       --key="#KERNEL_PANIC_BOOT_TIME" \
       --append="kernel.panic = 10"

# Copy Fake Cron
cp ./confs/fakecron /etc/init.d
chmod 755 /etc/init.d/fakecron

cp ./confs/fakecron.sh /usr/local/bin
chmod 755 /usr/local/bin/fakecron.sh

# Copy App Start Script
cp ./confs/rfid_app /etc/init.d
chmod 755 /etc/init.d/rfid_app

cp ./confs/rfid_app.sh /usr/local/bin
chmod 755 /usr/local/bin/rfid_app.sh

# Copy Git Update
cp ./confs/pull_git.sh /usr/local/bin
chmod 755 /usr/local/bin/pull_git.sh

cp -n /etc/rc.local ../original_confs/ # Don't overwrite if file exists with -n
cp ./confs/rc.local /etc
chmod 755 /etc/rc.local

########  POST-STOP SETUP ########

# Switch back to read only file system and enable watchdog
apt-get install -y watchdog
insserv watchdog
../app/helpers/mount_ro.sh
/etc/init.d/watchdog start

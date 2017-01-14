#!/bin/bash

find /bin        -mtime -1 -print | more
find /boot       -mtime -1 -print | more
#find /dev        -mtime -1 -print | more # no need as it's processor mapped
find /etc        -mtime -1 -print | more
#find /home       -mtime -1 -print | more # skip home as we use it
find /lib        -mtime -1 -print | more
find /lost+found -mtime -1 -print | more
find /media      -mtime -1 -print | more
find /mnt        -mtime -1 -print | more
find /opt        -mtime -1 -print | more
#find /proc      -mtime -1 -print | more  # no need as it's processor mapped
find /root       -mtime -1 -print | more
#find /run        -mtime -1 -print | more # no need as it's memory mapped
find /sbin       -mtime -1 -print | more
find /selinux    -mtime -1 -print | more
find /srv        -mtime -1 -print | more
#find /sys        -mtime -1 -print | more # no need as it's memory mapped
#find /tmp       -mtime -1 -print | more  # no need as it's memory mapped
find /usr        -mtime -1 -print | more
find /var        -mtime -1 -print | more




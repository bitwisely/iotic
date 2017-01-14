#!/bin/bash
# Mount device $1 to $2 path

echo "Mounting on .."
echo $1 $2
mkdir -p $2
umount -l $2 || /bin/true
mount -t vfat -o uid=1000,gid=1000,umask=007 /dev/$1 $2
#!/bin/bash

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=/home/treydock/backups/pihome

echo "Starting backup $DATE to $BACKUP_DIR"

#ssh -T -c aes128-gcm@openssh.com -o Compression=no -x pi@192.168.68.127 "sudo dd if=/dev/mmcblk0 bs=1M | gzip -" | pv | dd of=${BACKUP_DIR}/sdcard-${DATE}.gz
ssh -T -c aes128-gcm@openssh.com -o Compression=no -x pi@192.168.68.127 "sudo dd if=/dev/mmcblk0 bs=1M" | pv | dd of=${BACKUP_DIR}/sdcard-${DATE}
gzip ${BACKUP_DIR}/sdcard-${DATE}
# restore
#  gzip -dc ~/backups/pihome/sdcard.gz | sudo dd of=/dev/sde bs=1m conv=noerror,sync

rsync -avhx --numeric-ids \
  -e "ssh -T -c aes128-gcm@openssh.com -o Compression=no -x" \
  --rsync-path "sudo rsync" \
  --exclude '.cache' \
  --exclude 'Music' \
  pi@192.168.68.127:/home/pi/ \
  ${BACKUP_DIR}/home/pi/${DATE}

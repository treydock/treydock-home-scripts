#!/bin/bash

rsync -avm --progress --delete \
  --include "*/" --include "*.mp3" --exclude "*" \
  -e "ssh -T -c aes128-gcm@openssh.com -o Compression=no -x" \
  /home/treydock/Music/ \
  pi@192.168.68.127:/home/pi/Music/


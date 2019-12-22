#!/bin/bash

DISPLAY_ACTIVE=$(xset -display :0 q | grep -c 'Monitor is On')
if [ "$DISPLAY_ACTIVE" = "1" ]; then
  echo "1"
  exit 0
fi

HANDBRAKE=$(pgrep -c ghb)
if [ $HANDBRAKE -gt 0 ]; then
  echo "1"
  exit 0
fi

echo "0"
exit 0


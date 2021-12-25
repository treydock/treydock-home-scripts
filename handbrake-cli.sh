#!/bin/bash

INPUT="$1"
OUTPUT="$2"

if [[ "x${INPUT}" = "x" || "x${OUTPUT}" = "x" ]]; then
  echo "Must provide input and output"
  echo "handbrake-cli.sh INPUT OUTPUT"
fi

HandBrakeCLI --preset 'Fast 720p30' \
  --input "${INPUT}" --output "${OUTPUT}" \
  --optimize --align-av \
  --all-audio --ab 128 \
  --all-subtitles 

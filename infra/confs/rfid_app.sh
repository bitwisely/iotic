#!/usr/bin/env bash

# Wait 10 seconds
sleep 10

# Switch to project folder
{
  echo "RUNNING IN RELEASE MODE"
  cd /home/iodemo/demo-embedded/app
} || {
  echo "RUNNING IN DEBUG MODE"
  cd /home/iodemo/rfid/embedded/app
} || {
  echo "APP FOLDER MISSING!"
}

# Run the app
python appthread.py


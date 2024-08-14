#!/bin/bash

# Define the suffix of the daemon script we're looking for
DAEMON_INFIX="georeference.daemon.runner"

# Find all running processes matching the daemon suffix
running_daemon_pids=$(ps -ef | grep -v grep | grep "${DAEMON_INFIX}" | awk '{print $2}')

# If there are running daemons, kill the processes
if [ -n "$running_daemon_pids" ]; then
  echo "Killing running daemon process(es)..."
  echo $running_daemon_pids
  for pid in $running_daemon_pids; do
    kill -1 "$pid"
    echo "Killed process $pid"
  done
else
  echo "No running daemon found."
fi
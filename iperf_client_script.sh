#!/bin/bash

ALT_TIME="$1"
SERVER_IP="$2"
IPERF_PORT="$3"
CLIENT_PID="$4"
BYTES_T="150k"

# Run IPERF Command
run_iperf_for () {
  echo "Generating {$BYTES_T} bytes of traffic for {$1} seconds"
  iperf3 -c "$SERVER_IP" -p "$IPERF_PORT" -u -b $BYTES_T -t "$1"
}

# Check if client PID is still running
is_client_running() {
  echo "Checking if client is still running"
  local result
  result=$(ps --pid "$CLIENT_PID" || grep "$CLIENT_PID")

  if [[ -n "$result" ]]; then
    echo 1
  else
    echo 0
  fi
}

echo "Starting iPerf script"
# While client is running run the iPerf
while is_client_running; do
  run_iperf_for "$ALT_TIME"
  sleep "$ALT_TIME"
done
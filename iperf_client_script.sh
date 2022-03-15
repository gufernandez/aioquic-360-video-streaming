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
  if test -d /proc/"$CLIENT_PID"/; then
    echo 1
  else
    echo 0
  fi
}

echo "Starting iPerf script"
is_running=1
# While client is running run the iPerf
while [ $is_running -eq 1 ]; do
  run_iperf_for "$ALT_TIME"
  sleep "$ALT_TIME"
  echo "Check if client is still running"
  is_running="$(is_client_running)"
done
echo "Finished."
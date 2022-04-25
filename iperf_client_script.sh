#!/bin/bash

# Parâmetros
# - SERVER_IP: IP do servidor iperf
# - IPERF_PORT: Porta do servidor iperf
# - CLIENT_ID: PID do cliente de vídeo para ser aguardado o término
# - DURATION: Por quanto tempo o iperf deve rodar
# - TRAFFIC: Banda consumida pelo iperf constantemente

SERVER_IP="$1"
IPERF_PORT="$2"
DURATION="$3"
TRAFFIC="$4"

# Run IPERF Command
run_iperf_for () {
  echo "Generating ${2} bytes of traffic for ${1} seconds"
  iperf3 -c "$SERVER_IP" -p "$IPERF_PORT" -u -b "$2" -t "$1"
}

echo "--- Starting iPerf script ---"
echo "Constant traffic: ${CONSTANT_TRAFFIC}Bps"
is_running=1

# While client is running run the iPerf
while [ $is_running -eq 1 ]; do
  # Constant traffic
  if [ "$TRAFFIC" == "0" ]; then
    sleep "$DURATION"
  else
    run_iperf_for "$CONSTANT_DURATION" "$CONSTANT_TRAFFIC"
  fi
done
echo "Finished."
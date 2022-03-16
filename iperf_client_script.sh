#!/bin/bash

# Parâmetros
# - SERVER_IP: IP do servidor iperf
# - IPERF_PORT: Porta do servidor iperf
# - CLIENT_ID: PID do cliente de vídeo para ser aguardado o término
# - CONSTANT_DURATION: Por quanto tempo o iperf deve rodar
# - CONSTANT_TRAFFIC: Banda consumida pelo iperf constantemente
# - PEEK_DURATION: Por quanto tempo o pico ocorre
# - PEEK_TRAFFIC: Quanto de banda o pico consome

SERVER_IP="$1"
IPERF_PORT="$2"
CLIENT_PID="$3"
CONSTANT_DURATION="$4"
CONSTANT_TRAFFIC="$5"
PEEK_DURATION="$6"
PEEK_TRAFFIC="$7"

# Run IPERF Command
run_iperf_for () {
  echo "Generating ${2} bytes of traffic for ${1} seconds"
  iperf3 -c "$SERVER_IP" -p "$IPERF_PORT" -u -b "$2" -t "$1"
}

echo "--- Starting iPerf script ---"
echo "Constant traffic: ${CONSTANT_TRAFFIC}Bps"
is_running=1

# Check parameters
if [ -z "$PEEK_DURATION" ]; then
  if [ -n "$PEEK_TRAFFIC" ]; then
    echo "Needs peek bandwidth consumption and peek duration"
    exit
  fi
else
  echo "After ${CONSTANT_DURATION}s change to ${PEEK_TRAFFIC}Bps during ${PEEK_DURATION}s"
fi

# While client is running run the iPerf
while [ $is_running -eq 1 ]; do
  # Constant traffic
  if [ "$CONSTANT_TRAFFIC" == "0" ]; then
    sleep "$CONSTANT_DURATION"
  else
    run_iperf_for "$CONSTANT_DURATION" "$CONSTANT_TRAFFIC"
  fi

  # Peek
  if [ -n "$PEEK_TRAFFIC" ]; then
    run_iperf_for "$PEEK_DURATION" "$PEEK_TRAFFIC"
  fi
done
echo "Finished."
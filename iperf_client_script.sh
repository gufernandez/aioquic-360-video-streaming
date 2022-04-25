#!/bin/bash

# Parâmetros
# - SERVER_IP: IP do servidor iperf
# - IPERF_PORT: Porta do servidor iperf
# - CLIENT_ID: PID do cliente de vídeo para ser aguardado o término
# - DURATION: Por quanto tempo o iperf deve rodar
# - TRAFFIC: Banda consumida pelo iperf constantemente

SERVER_IP="$1"
IPERF_PORT="$2"
TRAFFIC1="$3"
TRAFFIC2="$4"
TRAFFIC3="$5"

echo "--- Starting iPerf script ---"
is_running=1

# While client is running run the iPerf
while [ $is_running -eq 1 ]; do
  iperf3 -c "$SERVER_IP" -p "$IPERF_PORT" -u -b "$TRAFFIC1" -t 20
  sleep 12
  iperf3 -c "$SERVER_IP" -p "$IPERF_PORT" -u -b "$TRAFFIC2" -t 16
  sleep 10
  iperf3 -c "$SERVER_IP" -p "$IPERF_PORT" -u -b "$TRAFFIC3" -t 14
  sleep 8
done
echo "Finished."
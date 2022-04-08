#!/bin/bash

# -mb > --mn-bandwidth: Bandwidth of mininet link
# -md > --mn-delay: Delay of mininet link
# -sq > --server-queue: Queuing on video Server
# -sp > --server-push: Is push enabled
# -da > --dash-algorithm: Dash algorithm
# -bd > --bg-duration: Duration of iperf background traffic (repeated)
# -bt > --bg-traffic: Bandwidth of iperf background traffic
# -pd > --peek-duration: Duration of iperf peek traffic (repeated)
# -pt > --peek-traffic: Bandwidth of iperf peek traffic

printf "================ Execução de Simulação com alternância nas filas ================\n\n"

push=1 # Push sempre ativado
dash="basic" # Bash sempre como basic
bg_d=60 #sec

# Sem picos
peek_d=0
peek_t="0"

id=1
#loads=(0.1 0.3)
loads=(0.3)
bands=(10.00 8.00) #Mbps
delays=("5ms" "10ms" "15ms" "20ms")
queues=("FIFO" "SP" "WFQ")

timestamp="date +%s"
exec_folder=$(eval "$timestamp")
mkdir out/"${exec_folder}"

for load in "${loads[@]}"; do
  for bw in "${bands[@]}"; do
    for delay in "${delays[@]}"; do
      for queue in "${queues[@]}"; do
        printf "*** Cenário %d ***\n" "$id"

        printf "BW: %f, Delay: %s, Queuing: %s, Push: %d" "$bw" "$delay" "$queue" "$push"
        printf ", Dash: %s, BG Traffic: %f\n" "$dash" "$load"

        for ((i = 0 ; i < 5 ; i++)); do
          exec_id="${id}-${i}"
          python3 mininet_config.py -id "${exec_id}" -mb "${bw}" -md "${delay}" -sq "${queue}" -sp ${push} -da ${dash} -bd ${bg_d} -bt "${load}" -pd ${peek_d} -pt ${peek_t} -out "${exec_folder}" > out/"${exec_folder}"/${exec_id}-exec.txt 2>&1
          rm -rf data/client_files_*
        done

        ((++id))
      done
    done
  done
done

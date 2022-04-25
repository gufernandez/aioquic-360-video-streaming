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
bg_d=80 #sec

id=1
loads=(0.1 0.3)
bands=(10.00 8.00) #Mbps
delays=("5ms" "20ms" "50ms" "100ms")
queues=("FIFO" "SP" "WFQ")
mn_buffer=(5 15)

timestamp="date +%s"
exec_folder=$(eval "$timestamp")
mkdir out/"${exec_folder}"

for load in "${loads[@]}"; do
  for bw in "${bands[@]}"; do
    for delay in "${delays[@]}"; do
      for queue in "${queues[@]}"; do
        for buffer_size in "${mn_buffer[@]}"; do
          printf "*** Cenário %d ***\n" "$id"

          printf "BW: %f, Delay: %s, Queuing: %s, Push: %d, Buffer Size: %d" "$bw" "$delay" "$queue" "$push" "$buffer_size"
          printf ", Dash: %s, BG Traffic: %f\n" "$dash" "$load"

          for ((i = 0 ; i < 5 ; i++)); do
            exec_id="${id}-${i}"
            python3 mininet_config.py -id "${exec_id}" -mb "${bw}" -md "${delay}" -mbf "${buffer_size}" -sq "${queue}" -sp ${push} -da ${dash} -bd ${bg_d} -bt "${load}" -out "${exec_folder}" > out/"${exec_folder}"/${exec_id}-exec.txt 2>&1
            rm -rf data/client_files_*
          done

          ((++id))
        done
      done
    done
  done
done

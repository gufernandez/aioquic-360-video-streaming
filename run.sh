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

printf "================ SIMULATION EXECUTION ================\n\n"

printf "*** First Set ***\n"

# Podemos criar um loop aqui

id=1
bw=100.00
delay="1ms"
queue="WFQ"
push=1
dash="basic"
bg_d=30
bg_t="5M"
peek_d=20
peek_t="80M"
printf "Execução %d. BW: %f, Delay: %s, Queuing: %s, Push: %d" "$id" "$bw" "$delay" "$queue" "$push"
printf ", Dash: %s, BG Duration: %d, BG Traffic: %s" "$dash" "$bg_d" "$bg_t"
printf ", Peek Duration: %d, Peek Traffic: %s\n" "$peek_d" "$peek_t"

python3 mininet_config.py -id ${id} -mb ${bw} -md ${delay} -sq ${queue} -sp ${push} -da ${dash} -bd ${bg_d} -bt ${bg_t} -pd ${peek_d} -pt ${peek_t} > out/${id}-exec.txt 2>&1

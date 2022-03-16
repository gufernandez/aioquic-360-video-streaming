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

python3 mininet_config.py -mb 100.00 -md "1ms" -sq "FIFO" -sp true -da "basic" -bd 30 -bt "5M" -pd 20 -pt "80M"
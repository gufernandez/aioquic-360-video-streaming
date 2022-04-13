#!/usr/bin/python
import argparse
import os
import re
import time

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel


# execfile('sflow-rt/extras/sflow.py')

class GEANTopo(Topo):
    "GEANT topology for traffic matrix"

    def __init__(self, bw: float, delay: str):
        # Initialize topology and default options
        Topo.__init__(self)

        # add nodes, switches first...
        switch_1 = self.addSwitch('s1')
        switch_2 = self.addSwitch('s2')

        # ... and now hosts
        host_1 = self.addHost('h1')
        host_2 = self.addHost('h2')

        # add edges between switch and corresponding host
        self.addLink(switch_1, host_1)
        self.addLink(switch_2, host_2)

        # add edges between switches
        self.addLink(switch_1, switch_2, bw=bw, delay=delay)  # , loss=1)


topos = {'geant': GEANTopo}


def launch(exec_id: str, mininet_bw: float, mininet_delay: str, server_queue: str, server_push: int, client_dash: str,
           iperf_const_duration: int, iperf_const_load: float, iperf_peek_duration: int, iperf_peek_load: float,
           out_folder: str):
    """
    Create and launch the network
    """
    # Create network
    print("*** Creating Network ***\n")
    topog = GEANTopo(mininet_bw, mininet_delay)
    net = Mininet(topo=topog, link=TCLink)

    # Run network
    print("*** Firing up Mininet ***\n")
    net.start()

    backbone = net.linksBetween(net.get('s1'), net.get('s2'))[0]

    # get initial rates
    init_rx, init_tx = get_rx_tx(backbone.intf1.ifconfig())

    # get initial time
    initial_timestamp = time.time()

    # Generate traffic
    print("*** Generating traffic from TMs ***\n")

    hosts = net.hosts

    server = hosts[0]
    client = hosts[1]

    print("\n*** Running server: "+server.IP()+" ***")
    server.cmd("export PYTHONPATH=$PYTHONPATH:/root/aioquic-360-video-streaming")

    push_flag = ""
    if server_push:
        push_flag = "-p"

    server_command = "python3 src/server.py -c cert/ssl_cert.pem -k cert/ssl_key.pem -q " + server_queue + " " \
                     + push_flag + " > out/" + out_folder + "/" + exec_id + "-server_out.txt &"
    print(server_command)
    server.cmd(server_command)
    server_pid = get_last_pid(server)
    print("-> Server running on process: ", server_pid)

    print("\n*** Running client: "+client.IP()+" ***")
    client.cmd("export PYTHONPATH=$PYTHONPATH:/root/aioquic-360-video-streaming")
    client_command = "python3 src/client.py -c cert/pycacert.pem "+server.IP()+":4433 -i data/user_input.csv -da " \
                     + client_dash + " > out/" + out_folder + "/" + exec_id + "-client_out.txt &"
    print(client_command)
    client.cmd(client_command)
    client_pid = get_last_pid(client)
    print("-> Client running on process: ", client_pid)

    print("\n*** Running iPerf server: "+server.IP()+" ***")
    iperf_port = "5002"
    iperf_server_command = "iperf3 -s -p " + iperf_port + " > out/" + out_folder + "/" \
                           + exec_id + "-iperf_server_out.txt &"
    print(iperf_server_command)
    server.cmd(iperf_server_command)
    iperf_server_pid = get_last_pid(server)
    print("-> iPerf server running on process: ", iperf_server_pid)

    const_traffic = str(mininet_bw * iperf_const_load) + "M"
    print("\n*** Running iPerf client with constant traffic of " + const_traffic + "bps ***")
    client.cmd("chmod 755 iperf_client_script.sh")
    iperf_params = " ".join([server.IP(), iperf_port, str(iperf_const_duration), const_traffic])
    optional_params = ""
    if iperf_peek_duration != 0 and iperf_peek_load != 0.0:
        peek_traffic = str(mininet_bw * iperf_peek_load) + "M"
        optional_params = " ".join([str(iperf_peek_duration), peek_traffic])
    iperf_command = "./iperf_client_script.sh "+iperf_params+" "+optional_params+" > out/" + out_folder + "/" \
                    + exec_id + "-iperf_client_out.txt &"
    print(iperf_command)
    client.cmd(iperf_command)
    iperf_client_pid = get_last_pid(client)
    print("-> iPerf client running on process: ", iperf_client_pid)

    print("\n*** Checking for client closure ***")

    is_running = True
    while is_running:
        process_command = "ps | grep " + client_pid
        process = client.cmd(process_command)
        if len(process) == 0:
            is_running = False
        else:
            client.cmd("sleep 1")

    print("\n\nCLIENT FINISHED\n\n")

    # get final rates
    final_rx, final_tx = get_rx_tx(backbone.intf1.ifconfig())

    # get final time
    closure_timestamp = time.time()

    total_rx = final_rx - init_rx
    total_tx = final_tx - init_tx
    execution_time = closure_timestamp - initial_timestamp

    print("*** Utilização do Canal ***\n")

    throughput = (total_rx + total_tx) / execution_time
    print("Taxa no canal: " + str(throughput) + "bits/s")
    print("Capacidade do link: " + str(mininet_bw) + "Mbps")

    channel_usage = throughput/(1048576*mininet_bw)
    print("Uso do canal: " + str(channel_usage))

    print("\n*** Killing remaining process ***\n")
    print("> Killing video server\n")
    server.cmd("kill -9 "+server_pid)
    print("> Killing iPerf server\n")
    server.cmd("kill -9 "+iperf_server_pid)
    print("> Killing iPerf client\n\n")
    client.cmd("kill -9 "+iperf_client_pid)
    print("*** Stopping Mininet ***")
    net.stop()


def get_last_pid(host):
    pid = host.cmd("echo $!")
    result = re.findall(r'\d+', pid)
    return result[0]


def get_rx_tx(ifconfig):
    rx_regex = re.compile(r"RX packets \d+  bytes (\d+)")
    tx_regex = re.compile(r"TX packets \d+  bytes (\d+)")

    # extract RX
    rx = rx_regex.search(ifconfig, re.MULTILINE).group(1)

    # extract TX
    tx = tx_regex.search(ifconfig, re.MULTILINE).group(1)

    # return values in bits
    return int(rx) * 8, int(tx) * 8


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mininet configuration and execution script")

    # Id
    parser.add_argument(
        "-id",
        type=str,
        default="",
        help="The identifier of the execution for logging purposes"
    )

    # Mininet parameters
    parser.add_argument(
        "-mb",
        "--mn-bandwidth",
        type=float,
        default=100.00,
        help="The channel bandwidth (float) of the mininet link in Mbps. Ex: '100.00'"
    )
    parser.add_argument(
        "-md",
        "--mn-delay",
        type=str,
        default="1ms",
        help="The channel delay of the mininet link. Ex: '1ms'"
    )

    # Server Parameters
    parser.add_argument(
        "-sq",
        "--server-queue",
        type=str,
        choices=['WFQ', 'SP', 'FIFO'],
        default="FIFO",
        help="The queuing algorithm used by the Video Server (WFQ, FIFO or SP)"
    )
    parser.add_argument(
        "-sp",
        "--server-push",
        type=int,
        choices=[0, 1],
        default=1,
        help="If server push is enabled or not"
    )

    # Client Parameters
    parser.add_argument(
        "-da",
        "--dash-algorithm",
        required=False,
        choices=['basic','basic2'],
        default="basic",
        type=str,
        help="dash algorithm (options: basic, basic2) - (defaults to basic)",
    )

    # iPerf Parameters
    parser.add_argument(
        "-bd",
        "--bg-duration",
        type=int,
        default=50,
        help="The duration of the background traffic on iPerf in seconds"
    )
    parser.add_argument(
        "-bt",
        "--bg-traffic",
        type=float,
        default=0.1,
        help="The bandwidth consumption by the background traffic on iPerf. Ex: 0.1 = 10%"
    )
    parser.add_argument(
        "-pd",
        "--peek-duration",
        type=int,
        default=0,
        help="The duration of the peek traffic on iPerf in seconds"
    )
    parser.add_argument(
        "-pt",
        "--peek-traffic",
        type=float,
        default=0,
        help="The bandwidth consumption by the peek traffic on iPerf in Bytes. Ex: 0.7 = 70%"
    )
    parser.add_argument(
        "-out",
        "--out-directory",
        type=str,
        default="default",
        help="The folder to store the scripts outputs"
    )
    args = parser.parse_args()

    # Cleaning up mininet
    os.system("sudo mn -c")
    # Tell mininet to print useful information
    setLogLevel('info')

    launch(exec_id=args.id, mininet_bw=args.mn_bandwidth, mininet_delay=args.mn_delay,
           server_queue=args.server_queue, server_push=args.server_push, client_dash=args.dash_algorithm,
           iperf_const_duration=args.bg_duration, iperf_const_load=args.bg_traffic,
           iperf_peek_duration=args.peek_duration, iperf_peek_load=args.peek_traffic, out_folder=args.out_directory)

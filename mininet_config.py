#!/usr/bin/python

import os

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI


# execfile('sflow-rt/extras/sflow.py')

class GEANTopo(Topo):
    "GEANT topology for traffic matrix"

    def __init__(self):
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
        self.addLink(switch_1, switch_2, bw=100.0, delay='1ms')  # , loss=1)


topos = {'geant': GEANTopo}


def launch():
    """
    Create and launch the network
    """
    # Create network
    print("*** Creating Network ***\n")
    topog = GEANTopo()
    net = Mininet(topo=topog, link=TCLink)

    # Run network
    print("*** Firing up Mininet ***\n")
    net.start()

    # Generate traffic
    print("*** Generating traffic from TMs ***\n")

    hosts = net.hosts

    server = hosts[0]
    client = hosts[1]

    print("*** Running server: "+server.IP()+" ***\n")
    server.cmd("export PYTHONPATH=$PYTHONPATH:/root/aioquic-360-video-streaming")
    server.cmd("python3 src/server.py -c cert/ssl_cert.pem -k cert/ssl_key.pem -q 'WFQ' -p >> data/server_out.txt &")
    server_pid = server.cmd("echo $!")
    print("-> Server running on process: ", server_pid)

    print("*** Running client: "+client.IP()+" ***\n")
    client.cmd("export PYTHONPATH=$PYTHONPATH:/root/aioquic-360-video-streaming")
    client.cmd("python3 src/client.py -c cert/pycacert.pem "+server.IP()+":4433 -i data/user_input.csv "
                                                                         ">> client_out.txt &")
    client_pid = client.cmd("echo $!")
    print("-> Client running on process: ", client_pid)

    print("*** Running iPerf server: "+server.IP()+" ***\n")
    iperf_port = "5002"
    server.cmd("iperf3 -s -p " + iperf_port + "&")
    iperf_server_pid = server.cmd("echo $!")
    print("-> iPerf server running on process: ", iperf_server_pid)

    constant_duration = "25"
    constant_traffic = "5M"
    peek_duration = "20"
    peek_traffic = "70M"

    print("*** Running iPerf client with constant traffic of "+constant_traffic+"Bps ***\n")
    client.cmd("chmod 755 iperf_client_script.sh")
    iperf_params = " ".join([server.IP(), iperf_port, constant_duration, constant_traffic])
    optional_params = ""
    if peek_duration and peek_traffic:
        optional_params = " ".join([peek_duration, peek_traffic])
    iperf_command = "./iperf_client_script.sh "+iperf_params+optional_params+" &".replace("\n", "")
    print("Running command: ", iperf_command)
    print(client.cmd(iperf_command))
    iperf_client_pid = client.cmd("echo $!")
    print("-> iPerf client running on process: ", iperf_client_pid)

    print("*** Checking for client closure ***\n")

    is_running = True
    while is_running:
        process_command = "pgrep python3 -s ", client_pid
        print(process_command)
        process = client.cmd(process_command)
        print(process)
        if len(process) == 0:
            is_running = False

    print("*** Stopping Mininet ***")
    net.stop()


if __name__ == '__main__':
    # Cleaning up mininet
    os.system("sudo mn -c")
    # Tell mininet to print useful information
    setLogLevel('info')

    launch()

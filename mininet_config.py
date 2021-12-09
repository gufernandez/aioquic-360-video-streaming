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
        self.addLink(switch_1, switch_2, bw=100.0, delay='100ms')  # , loss=1)


topos = {'geant': GEANTopo}


def launch():
    """
    Create and launch the network
    """
    # Create network
    print("*** Creating Network ***")
    topog = GEANTopo()
    net = Mininet(topo=topog, link=TCLink)

    # Run network
    print("*** Firing up Mininet ***")
    net.start()

    # Generate traffic
    print("*** Generating traffic from TMs ***\n")

    hosts = net.hosts

    server = hosts[0]
    client = hosts[1]

    print("*** Running server ***\n")
    server.cmd("export PYTHONPATH=$PYTHONPATH:/root/aioquic-360-video-streaming")
    server.cmd("nohup python3 src/server.py -c 'cert/ssl_cert.pem' -k 'cert/ssl_key.pem' -q 'WFQ' >> server_out.txt &")
    #server.cmd("nohup dist/server/server -c 'cert/ssl_cert.pem' -k 'cert/ssl_key.pem' >> server_out.txt &")

    print("*** Running client ***\n")
    client.cmd("export PYTHONPATH=$PYTHONPATH:/root/aioquic-360-video-streaming")
    client.cmd("python3 src/client.py -c cert/pycacert.pem 127.0.0.1:4433 -i data/user_input.csv >> client_out.txt")
    #client.cmd("dist/client/client -c 'cert/pycacert.pem' -i 'data/user_input.csv' -u 'wss://10.0.0.1:4433' -da basic2 >> client_out.txt")

    # Start CLI
    CLI(net)

    print("*** Stopping Mininet ***")
    net.stop()


if __name__ == '__main__':
    # Cleaning up mininet
    os.system("sudo mn -c")
    # Tell mininet to print useful information
    setLogLevel('info')

    launch()

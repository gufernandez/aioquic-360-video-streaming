from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo

def run():
    net = Mininet(topo=SingleSwitchTopo())
    net.start()

    CLI(net)
    net.pingAll()
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
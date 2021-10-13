from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo

def run():
    net = Mininet(topo=SingleSwitchTopo())
    net.start()
    hosts = net.hosts

    print("Starting server...")
    server = hosts[0]
    server.cmd('python3 server.py -c ../cert/ssl_cert.pem -k ../cert/ssl_key.pem -q "WFQ" &')
    print(f'Server {server.name} started!')

    print("Starting client...")
    client = hosts[1]
    out_file = 'out.txt'
    client.cmd('echo > ', out_file)
    pid = int(client.cmd(f'python3 client.py -c ../cert/pycacert.pem "wss://{server.IP()}:4433" -i ../data/user_input.csv'))
    client.cmd('wait', pid)
    net.stop()

# if the script is run directly (sudo custom/optical.py):
if __name__ == '__main__':
    setLogLevel('info')
    run()
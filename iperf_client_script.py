#!/usr/bin/python
import argparse
import subprocess
import time


def run_iperf(server_ip: str, server_port: str, band: str, exec_time: str):
    subprocess.run(["iperf3", "-c", server_ip, "-p", server_port, "-u", "-b", band, "-t", exec_time],
                   capture_output=True)


def get_load(load_traffic: float, multiplier: float):
    return str(load_traffic * multiplier) + "M"


def generate_load(server_ip: str, server_port: str, duration: int, bandwidth: float, load: float):

    load_traffic = bandwidth * load
    load_m1 = 2.0
    load_m3 = 1.625
    load_m5 = 1.0

    d1 = 20/80 * duration
    d2 = 12/80 * duration
    d3 = 16/80 * duration
    d4 = 10/80 * duration
    d5 = 14/80 * duration
    d6 = 8/80 * duration

    state = 1
    while True:
        if state == 1:
            run_iperf(server_ip, server_port, get_load(load_traffic, load_m1), str(d1))
            state = 2
        elif state == 2:
            time.sleep(d2)
            state = 3
        elif state == 3:
            run_iperf(server_ip, server_port, get_load(load_traffic, load_m3), str(d3))
            state = 4
        elif state == 4:
            time.sleep(d4)
            state = 5
        elif state == 5:
            run_iperf(server_ip, server_port, get_load(load_traffic, load_m5), str(d5))
            state = 6
        elif state == 6:
            time.sleep(d6)
            state = 1
        else:
            print("Erro na execução do IPerf")
            return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script to run Iperf load generator")

    # Id
    parser.add_argument(
        "-ip",
        "--server-ip",
        type=str,
        help="The server IP to send the traffic"
    )
    parser.add_argument(
        "-port",
        "--server-port",
        type=str,
        help="The port of the iperf server"
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        help="The duration of the script execution"
    )
    parser.add_argument(
        "-mb",
        "--mn-bandwidth",
        type=float,
        help="The channel bandwidth (float) of the mininet link in Mbps. Ex: '100.00'"
    )
    parser.add_argument(
        "-l",
        "--load",
        type=float,
        help="The load that must be generated"
    )

    args = parser.parse_args()

    generate_load(server_ip=args.server_ip, server_port=args.server_port, duration=args.duration,
                  bandwidth=args.mn_bandwidth, load=args.load)

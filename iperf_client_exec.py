#!/usr/bin/python
import argparse
import os
import random
import statistics
import subprocess

RUN_TIMES = 5


def iperf_execution(ip, port, load, bw):
    on_avg = 12
    off_avg = 4
    duration = 80
    on_values, off_values = get_random_iperf_params(on_avg, off_avg)
    load_traffic = load*bw*duration/on_avg
    load_traffic = str(load_traffic) + "M"
    print(on_values)
    print(off_values)
    print(load_traffic)
    for i in range(RUN_TIMES):
        sleep_time = str(off_values[i])
        run_time = str(on_values[i])
        iperf_command = "iperf3 -c " + ip + " -p " + port + " -u -b " + load_traffic + " -t " + run_time
        returned_text = subprocess.check_output(iperf_command)
        print(returned_text)
        os.system("sleep " + sleep_time)


def get_random_iperf_params(on_avg, off_avg):
    def warmup(a, b, size=100000):
        samples = []
        for i in range(size):
            c = random.uniform(a, b)
            samples.append(c)

        return samples

    # Encontra slices de tamanho slice_size na lista
    # samples que tem media igual a
    # média desejada (avg)
    def trail(a=0, b=2, avg=10, size=1000000, slice_size=RUN_TIMES, slice_count=3):
        random_lists = []
        samples = warmup(a, b, size)
        for i in range(int(size / slice_size)):
            picked = [int(x * avg) for x in samples[slice_size * i:(i + 1) * slice_size]]
            if (statistics.mean(picked) == avg) and (slice_count > 0):
                random_lists.append(picked)
                slice_count -= 1
        return random_lists

    on_list = trail(avg=on_avg)
    off_list = trail(avg=off_avg)

    i_on = random.randint(0, len(on_list))
    i_off = random.randint(0, len(off_list))

    return on_list[i_on], off_list[i_off]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mininet configuration and execution script")

    parser.add_argument(
        "-ip",
        type=str,
        help="The iPerf server IP address."
    )
    parser.add_argument(
        "-p",
        type=str,
        help="The iPerf server Port."
    )

    parser.add_argument(
        "-mb",
        "--mn-bandwidth",
        type=float,
        default=100.00,
        help="The channel bandwidth (float) of the mininet link in Mbps. Ex: '100.00'"
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=80,
        help="The duration of the background traffic on iPerf in seconds"
    )
    parser.add_argument(
        "-l",
        "--load",
        type=float,
        default=0,
        help="The bandwidth consumption by the background traffic on iPerf. Ex: 0.1 = 10%"
    )
    parser.add_argument(
        "-out",
        "--out-directory",
        type=str,
        help="The folder to store the scripts outputs"
    )
    args = parser.parse_args()

    iperf_execution(ip=args.ip, port=args.p, bw=args.mn_bandwidth, load=args.load)

#!/usr/bin/python
import argparse
import os
import random
import statistics

RUN_TIMES = 5
TO_FILE = " >> "


def iperf_execution(ip, port, load, bw, out_file):
    duration = 60

    time_values = get_random_iperf_params(bw, duration, load)

    for run_time, sleep_time, traffic in time_values:
        sleep_time = str(sleep_time)
        run_time = str(run_time)
        load_traffic = str(traffic) + "M"

        iperf_command = "iperf3 -c " + ip + " -p " + port + " -u -b " + load_traffic \
                        + " -t " + run_time + TO_FILE + out_file
        echo_command(iperf_command, out_file)
        os.system(iperf_command)
        echo_command("Sleeping " + sleep_time + " seconds.", out_file)
        os.system("sleep " + sleep_time)


def get_random_iperf_params(C, T, lbda):
    # sorteia size numeros entre a e b, retornando a
    # lista de numeros
    def warmup(a, b, size=1000000):
        samples = []
        for i in range(size):
            c = random.uniform(a, b)
            samples.append(c)

        return samples

    # Encontra slices de tamanho slice_size na lista
    # samples que tem media igual a
    # média desejada (avg)
    def trail(a=0, b=2, t_avg=10, t_avg_on=4, periodo_ativo=5, taxa_media=3.0, samples_count=5, BW=10):
        size = 1000000
        samples = warmup(a, b, size)

        time_list = []
        for i in range(int(size)):
            if samples_count > 0:
                picked = [int(x) for x in samples[i:(i + periodo_ativo)]]
                if statistics.mean(picked) == t_avg_on:
                    par_on_off = []
                    total = 0
                    for x in picked:
                        rate = min(round((float(t_avg) / float(x)) * taxa_media, 2), round(float(BW), 2))
                        par_on_off.append((x, t_avg - x, rate))
                        thelatter = par_on_off[len(par_on_off) - 1]
                        total += thelatter[0] * thelatter[2]
                    time_list.append(par_on_off)
                    samples_count -= 1
        return time_list

    N = 10  # numeros de vezes que a fonte ficara ativa
    R = C * lbda  # taxa media de bits qdo a fonte fica ativa

    t_avg = int((C * T * lbda) / (N * R))
    t_avg_on = max(round((2.0 * t_avg) / 3.0), round(C / R))

    periods = trail(a=round(C / R), b=t_avg, t_avg=t_avg, t_avg_on=t_avg_on, periodo_ativo=N, taxa_media=R, BW=C)

    i = random.randint(0, len(periods)-1)
    return periods[i]


def echo_command(text, out_file):
    os.system("echo " + text + TO_FILE + out_file)


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
        "-l",
        "--load",
        type=float,
        default=0,
        help="The bandwidth consumption by the background traffic on iPerf. Ex: 0.1 = 10%"
    )
    parser.add_argument(
        "-o",
        "--out-file",
        type=str,
        help="The file to store the scripts outputs"
    )
    args = parser.parse_args()

    iperf_execution(ip=args.ip, port=args.p, bw=args.mn_bandwidth, load=args.load, out_file=args.out_file)

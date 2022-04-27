#!/usr/bin/python
import re

REBUFFER_PATTERN = r'Filling buffer from segment (\d+) to segment (\d+)'
TOTAL_MISSING_RATIO_PATTERN = r'Missing ratio total: (\d+.\d+)%'
TOTAL_POV_MISSING_RATIO_PATTERN = r'(\d+.\d+)%'
BITRATE_PATTERN = r'(\d+.\d+)'

START_CHANNEL_PATTERN = r'(do Canal)'
TRAFFIC_PATTERN = r'(\d+.\d+)bits/s'
LINK_WIDTH_PATTERN = r'(\d+.\d+)Mbps'
CHANNEL_USAGE_PATTERN = r'(\d+.\d+)'
LINK_PATTERNS = [START_CHANNEL_PATTERN, TRAFFIC_PATTERN, LINK_WIDTH_PATTERN, CHANNEL_USAGE_PATTERN]

IPERF_START_PATTERN = r'(Total Datagrams)'
DATAGRAM_PATTERN = r'(\d+)  $'
IPERF_END_PATTERN = r'iperf Done.'
IPERF_PATTERNS = [IPERF_START_PATTERN, DATAGRAM_PATTERN]

DATAGRAM_SIZE = 65536  # bits

LOADS = [0.1, 0.3]
BANDS = [10.00, 8.00]  # Mbps
DELAYS = ["5ms", "20ms", "50ms", "100ms"]
QUEUES = ["FIFO", "SP", "WFQ"]

N_EXECUTION = 5


def mean(number_list):
    return round(sum(number_list) / len(number_list), 3)


def mean_percentage(number_list):
    return round(sum(number_list) / (len(number_list) * 100), 5)


def get_att_id(cen_id, mod, div):
    return int(((cen_id - 1) % mod) / div)


def print_row():
    row = "; ".join([str(cenario_id), str(LOADS[loads_id]), str(BANDS[bands_id]), DELAYS[delay_id], QUEUES[queue_id],
                     str(rebuffering_count_mean), str(rebuffered_secs_mean), str(missing_ratio_total_mean),
                     str(missing_ratio_pov_mean), str(bitrate_avg_mean), str(total_channel_usage_mean),
                     str(application_channel_usage_mean), str(iperf_usage_mean)])
    row = row.replace('.', ',')
    print(row)


if __name__ == '__main__':
    args_dir = 1650902526
    user_dir = "./out/" + str(args_dir) + "/"

    print("id; load_per; channel_bandwidth; delay_ms; queue; rebuffer_count; rebuffer_s; miss_ratio_all_per; "
          "miss_ratio_pov_per; bitrate_avg; total_channel_usage_per; app_channel_usage_per; iperf_channel_usage_per")

    for cenario_id in range(1, 49):
        rebuffering_count = []
        rebuffered_secs = []
        missing_ratio_total = []
        missing_ratio_pov = []
        bitrate_avg = []
        channel_bw = 0
        total_channel_traffic = []
        total_channel_usage = []
        iperf_usage = []
        application_channel_usage = []

        for i in range(N_EXECUTION):
            # CLIENT FILE: RATIOS and BITRATE
            file_name = user_dir + '-'.join([str(cenario_id), str(i), "client_out.txt"])
            with open(file_name) as f:
                lines = f.readlines()

                reb_c = 0
                reb_sec = 0
                state = 1  # Looking for rebuffer
                for line in lines:
                    if state == 1:
                        result = re.findall(REBUFFER_PATTERN, line)

                        if result:
                            reb_c += 1
                            init_b, end_b = result[0]
                            reb_sec += (int(end_b) - int(init_b))
                        else:
                            result = re.findall(TOTAL_MISSING_RATIO_PATTERN, line)

                            if result:
                                missing_ratio_total.append(float(result[0]))
                                rebuffering_count.append(reb_c)
                                rebuffered_secs.append(reb_sec)
                                state = 2

                    elif state == 2:
                        result = re.findall(TOTAL_POV_MISSING_RATIO_PATTERN, line)
                        if result:
                            missing_ratio_pov.append(float(result[0]))
                            state = 3
                    elif state == 7:
                        result = re.findall(BITRATE_PATTERN, line)
                        if result:
                            bitrate_avg.append(float(result[0]))
                            break
                    else:
                        state += 1

            # EXEC FILE: Channel Usage
            file_name = user_dir + '-'.join([str(cenario_id), str(i), "exec.txt"])
            with open(file_name) as f:

                state = 0
                lines = f.readlines()
                for line in lines:
                    result = re.findall(LINK_PATTERNS[state], line)

                    if result:
                        if state == 1:
                            total_channel_traffic.append(float(result[0]))
                        elif state == 2:
                            channel_bw = float(result[0])
                        elif state == 3:
                            total_channel_usage.append(float(result[0]))
                            break
                        state += 1

            # IPERF FILE: Channel Usage by Iperf
            file_name = user_dir + '-'.join([str(cenario_id), str(i), "iperf_client_out.txt"])
            with open(file_name) as f:
                lines = f.readlines()

                state = 0
                iperf_datagrams = 0
                iperf_seconds = 0
                for line in lines:
                    if state == 1:
                        end = re.findall(IPERF_END_PATTERN, line)
                        if end:
                            state = 0
                            continue

                    result = re.findall(IPERF_PATTERNS[state], line)

                    if result:
                        if state == 0:
                            state = 1
                        elif state == 1:
                            iperf_datagrams += int(result[0])
                            iperf_seconds += 1

                iperf_throughput = iperf_datagrams * DATAGRAM_SIZE / iperf_seconds
                iperf_usage.append(iperf_throughput / (1048576 * channel_bw))

        for i in range(N_EXECUTION):
            application_channel_usage.append(total_channel_usage[i] - iperf_usage[i])

        rebuffering_count_mean = mean(rebuffering_count)
        rebuffered_secs_mean = mean(rebuffered_secs)
        missing_ratio_total_mean = mean_percentage(missing_ratio_total)
        missing_ratio_pov_mean = mean_percentage(missing_ratio_pov)
        bitrate_avg_mean = mean(bitrate_avg)
        iperf_usage_mean = mean(iperf_usage)
        total_channel_usage_mean = mean(total_channel_usage)
        application_channel_usage_mean = mean(application_channel_usage)

        mod = len(QUEUES)
        div = 1
        queue_id = get_att_id(cenario_id, mod, div)

        div = mod
        mod = mod * len(DELAYS)
        delay_id = get_att_id(cenario_id, mod, div)

        div = mod
        mod = mod * len(BANDS)
        bands_id = get_att_id(cenario_id, mod, div)

        div = mod
        mod = mod * len(LOADS)
        loads_id = get_att_id(cenario_id, mod, div)

        print_row()

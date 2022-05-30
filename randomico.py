import random
import statistics

RUN_TIMES = 5


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

    i_on = random.randint(0, len(on_list)-1)
    i_off = random.randint(0, len(off_list)-1)

    return on_list[i_on], off_list[i_off]


if __name__ == "__main__":
    on_avg = 8
    off_avg = 4
    duration = 60
    print(get_random_iperf_params(on_avg, off_avg))
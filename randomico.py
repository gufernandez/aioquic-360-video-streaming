
# sorteia size numeros entre a e b, retornando a
# lista de numeros
from random import uniform
from statistics import mean


def warmup(a, b, size=100000):
    samples =[]
    for i in range(size):
        c = uniform(a, b)
        samples.append(c)

    return samples


# Encontra slices de tamanho slice_size na lista
# samples que tem media igual a
# média desejada (avg)
def trail(a=0, b=2, avg=10, size=1000000, slice_size=5, slice_count=3):
    lists = []
    samples = warmup(a, b, size)
    for i in range(int(size / slice_size)):
        picked = [int(x * avg) for x in samples[slice_size * i:(i + 1) * slice_size]]
        if (mean(picked) == avg) and (slice_count > 0):
            lists.append(picked)
            slice_count -= 1
    return lists


if __name__ == "__main__":
    print("periodo ON")
    print(trail(avg=60))

    print("periodo OFF")
    trail(avg=20)

    #total = 80
    #banda_load*TEMPO_ON = LOAD*BANDA_CANAL*TEMPO_TOTAL
    #banda_load = LOAD*BANDA_CANAL*TEMPO_TOTAL/TEMPO_ON

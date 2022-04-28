from random import *
from statistics import *


# sorteia size numeros entre a e b, retornando a
# lista de numeros
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
    samples = warmup(a, b, size)
    print("SAMPLES")
    print(samples)
    for i in range(int(size/slice_size)):
        picked = [int(x*avg) for x in samples[slice_size*i:(i+1)*slice_size]]
        if (mean(picked) == avg) and (slice_count>0):
            print(picked)
            slice_count -= 1


if __name__ == "__main__":
    print("periodo ON")
    trail(avg=6)

    print("periodo OFF")
    trail(avg=3)

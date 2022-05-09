from random import *
from statistics import *
import random


# sorteia size numeros entre a e b, retornando a
# lista de numeros
def warmup(a, b, size=1000000):
    samples = []
    for i in range(size):
        c = uniform(a, b)
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
            if mean(picked) == t_avg_on:
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


if __name__ == "__main__":
    # print("periodos ON")
    C = 10  # capacidade do canal
    T = 60  # duracao da sessao de video
    lbda = 0.3  # media ocupacao com trafego background

    N = 10  # numeros de vezes que a fonte ficara ativa
    R = C * lbda  # taxa media de bits qdo a fonte fica ativa

    t_avg = int((C * T * lbda) / (N * R))
    t_avg_on = max(round((2.0 * t_avg) / 3.0), round(C / R))  # muito ativa
    # t_avg_on = max(int(t_avg/2.0),int(C/R)) # muito esporádica

    periods = trail(a=round(C / R), b=t_avg, t_avg=t_avg, t_avg_on=t_avg_on, periodo_ativo=N, taxa_media=R, BW=C)

    i = random.randint(0, len(periods)-1)

    for on, off, traffic in periods[i]:
        print(on, off, traffic)

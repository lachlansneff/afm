import matplotlib.pyplot as plt
import sys
from vcdvcd import VCDVCD
from bitstring import BitArray

vcd = VCDVCD(sys.argv[1])
# times, amplitudes = zip(*vcd['top.sin'].tv)
# print(amplitudes)

def plot(name):
    x = vcd[name]
    times, amplitudes = zip(*x.tv)

    # print(amplitudes)
    size = int(x.size)

    amplitudes = list(map(lambda s: BitArray(bin=s.zfill(size)).uint, amplitudes))
    times = list(map(lambda t: t * vcd.timescale["magnitude"], times))

    plt.plot(times, amplitudes)

plot('top.sin')
# plot('top.cos')

plt.xlabel('timestamp')
plt.ylabel('amplitude')
plt.show()

import gc
import struct


def read(i2c, addr):
    response = i2c.readfrom(addr, 2)
    status_bits = (response[0] & 0b11000000) >> 6
    # 2 most significant bits are status bits; should both be zero.
    #
    # See https://sensing.honeywell.com/honeywell-sensing-hsc-ssc-abp-fsa-board-mount-diagnostics-technical-note-008264-2-en.pdf
    if status_bits != 0:
        gc.collect()
        raise IOError('Error reading pressure; status_bits=%s' %
                      bin(status_bits))
    value = struct.unpack('>h', response)[0]
    pressure_min = 0
    pressure_max = 60
    gc.collect()
    return ((value / (2 ** 14) - .1) / .8 * (pressure_max - pressure_min) +
            pressure_min)


class HoneywellSSC:
    def __init__(self, i2c, addr=0x28):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        return read(self.i2c, self.addr)

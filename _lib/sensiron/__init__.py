import gc
import struct


def crc8(buf):
    if len(buf) == 0:
        return 0

    crc = 0xFF
    for byte in buf:
        for bit in range(0, 8):
            if (byte ^ crc) & 0x80 :
                crc = (crc << 1) ^ 0x31
            else:
                crc = ( crc << 1 )
            byte = byte << 1
        crc = crc & 0xFF
    return crc


class CrcError(Exception):
    pass            


class SLF3S_1300F:
    # https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/0_Datasheets/Liquid_Flow/Sensirion_Liquid_Flow_Sensor_SLF3S-1300F_Datasheet_EN_D1.pdf
    def __init__(self, i2c, addr=0x08):
        self.i2c = i2c
        self.addr = addr

    def crc_check(self, result):
        for i in range(0, len(result), 3):
            if crc8(result[i:i+2]) != result[i+2]:
                raise CrcError

    def get_device_info(self):
        self.i2c.writeto(self.addr, b'\x36\x7C')
        self.i2c.writeto(self.addr, b'\xE1\x02')
        result = self.i2c.readfrom(self.addr, 18)
        self.crc_check(result)
        return {'product_number': struct.unpack('L', result[0:2] + result[3:5])[0],
                'serial_number': struct.unpack('Q', result[6:8] + result[9:11] + result[12:14] + result[15:17])[0]}

    @property
    def product_number(self):
        return self.get_device_info()['product_number']

    @property
    def serial_number(self):
        return self.get_device_info()['serial_number']

    def start_continuous_measurement(self, medium='water'):
        if medium == 'water':
            self.i2c.writeto(self.addr, b'\x36\x08')
        elif medium == 'isopropyl alcolol':
            self.i2c.writeto(self.addr, b'\x36\x15')
        else:
            raise NameError

    def stop_continuous_measurement(self):
        self.i2c.writeto(self.addr, b'\x3F\xF9')

    def soft_reset(self):
        self.i2c.write(b'\x00\x06')

    def get_measurement(self):
        result = self.i2c.readfrom(self.addr, 9)
        self.crc_check(result)
        flags = struct.unpack('h', result[6:8])[0]
        return {'flow': struct.unpack('h', result[0:2])[0] / 500.0, # mL/min
                'temperature': struct.unpack('h', result[3:5])[0] / 200.0, # degrees C
                'air-in-line': flags & 1,
                'high flow': flags >> 1 & 1,
                'exp smoothing active': flags >> 5 & 1}
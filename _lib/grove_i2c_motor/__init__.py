import gc
import time

from base_node import BaseDriver, replace

IN1, IN2, IN3, IN4 = list(range(4, 8))
ENA, ENB = 9, 10


def initialize(grove_motor, **kwargs):
    '''
    Initialize pin modes and default states:

     - All output control pins defined as OUTPUT mode, default LOW
     - All ENABLE pins default to HIGH
    '''
    config = grove_motor.config
    print(config)
    pin_mode_bytes = bytearray(config.pin_mode_bytes)
    pin_state_bytes = bytearray(config.pin_state_bytes)
    print('mode:', [v for v in pin_mode_bytes])
    print('state:', [v for v in pin_state_bytes])

    for pin in (IN1, IN2, IN3, IN4, ENA, ENB):
        port = pin // 8
        port_pin = pin % 8
        pin_mode_bytes[port] |= 1 << port_pin
        if pin in (ENA, ENB):
            pin_state_bytes[port] |= 1 << port_pin
        else:
            pin_state_bytes[port] &= ~(1 << port_pin)
    gc.collect()
    print(gc.mem_free())

    print('mode:', [v for v in pin_mode_bytes])
    print('state:', [v for v in pin_state_bytes])
    new_config = replace(config, pin_mode_bytes=pin_mode_bytes,
                         pin_state_bytes=pin_state_bytes, **kwargs)
    print(new_config)
    grove_motor.config = new_config
    # Re-initialize according to the new configuration.
    grove_motor.load_config()


def identify(self):
    gc.collect()
    for pin in (ENA, ENB):
        self.digital_write(pin, 0)
        gc.collect()
    for pin in (IN1, IN2, IN3, IN4):
        self.digital_write(pin, 0)
        gc.collect()
    for pin in (IN1, IN2, IN3, IN4):
        self.digital_write(pin, 1)
        gc.collect()
    for pin in (IN1, IN2, IN3, IN4):
        self.digital_write(pin, 0)
        gc.collect()
    for pin in (ENA, ENB):
        self.digital_write(pin, 1)
        gc.collect()

import _thread
import functools as ft
import gc
import time
import uasyncio as asyncio
gc.collect()

from base_node import BaseDriver, replace
import grove_i2c_motor as gm
import lvgl as lv


class Pump():
    def __init__(self, i2c, i2c_address, pin, on_done_callback=None, on_ms=50,
                 off_ms=150):
        '''
        Parameters
        ----------
        i2c : machine.I2C
            I2C driver handle.
        i2c_address : int
            I2C address.
        pin : int
            Motor output pin (e.g., ``grove_i2c_motor.IN1``).
        on_done_callback : function
            Callback function to be called when the specified number of pulses
            have been executed.
        pulses : int
            Number of pulses.
        on_ms : int, optional
            Duration for which output should be turned **on**, in milliseconds.
        off_ms : int, optional
            Duration for which output should be turned **off**, in milliseconds.
        '''
        self.i2c = i2c
        self.i2c_address = i2c_address
        self.pin = pin
        self.on_done_callback = on_done_callback
        self.on_ms = on_ms
        self.off_ms = off_ms
        self.pulses = 0

    def stop(self):
        self.pulses = 0
        if self.on_done_callback:
            self.on_done_callback()

    async def execute(self, pulses):
        driver = gm.BaseDriver(self.i2c, self.i2c_address)
        await asyncio.sleep_ms(0)
        self.pulses = pulses
        try:
            while self.pulses > 0:
                self.pulses -= 1
                driver.digital_write(self.pin, 1)
                await asyncio.sleep_ms(self.on_ms)
                driver.digital_write(self.pin, 0)
                await asyncio.sleep_ms(self.off_ms)
        except Exception as exception:
            print('Error pumping:', exception)
        self.stop()

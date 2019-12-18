import _thread
import functools as ft
import gc
import time
import uasyncio as asyncio
gc.collect()

from base_node import BaseDriver, replace
import grove_i2c_motor as gm
import lvgl as lv


async def pump(i2c, i2c_address, pin, pulses, on_ms=50, off_ms=150):
    '''
    Parameters
    ----------
    i2c : machine.I2C
        I2C driver handle.
    i2c_address : int
        I2C address.
    pin : int
        Motor output pin (e.g., ``grove_i2c_motor.IN1``).
    pulses : int
        Number of pulses.
    on_ms : int, optional
        Duration for which output should be turned **on**, in milliseconds.
    off_ms : int, optional
        Duration for which output should be turned **off**, in milliseconds.
    '''
    driver = gm.BaseDriver(i2c, i2c_address)
    await asyncio.sleep_ms(0)
    for i in range(pulses):
        driver.digital_write(pin, 1)
        await asyncio.sleep_ms(on_ms)
        driver.digital_write(pin, 0)
        await asyncio.sleep_ms(off_ms)
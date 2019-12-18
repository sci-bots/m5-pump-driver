import gc
import uasyncio as asyncio
gc.collect()

from base_node import BaseDriver
import lvgl as lv


async def set_valve(i2c, i2c_address, pin, state):
    '''
    Parameters
    ----------
    i2c : machine.I2C
        I2C driver handle.
    i2c_address : int
        I2C address.
    pin : int
        Motor output pin (e.g., ``grove_i2c_motor.IN1``).
    state : bool
        If ``False`` set to ``A`` branch. Otherwise, set to ``B`` branch.
    '''
    driver = BaseDriver(i2c, i2c_address)
    await asyncio.sleep_ms(0)
    driver.digital_write(pin, state)
    del driver
    gc.collect()
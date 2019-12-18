from collections import OrderedDict
import _thread
import gc
import sys
sys.path.insert(0, '/_lib')  # pragma: no cover
import time
import uasyncio as asyncio

from base_node import BaseDriver, replace
from machine import I2C, Pin
from lvgl_helpers import InputsTabView
from m5_lvgl import M5ili9341, ButtonsInputEncoder, EncoderInputDriver
from pump import pump
from valve import set_valve
import functools as ft
import grove_i2c_motor as gm
import lvgl as lv

import ui


def initialize(driver, **kwargs):
    config = driver.config
    print(config)
    new_config = replace(config, **kwargs)
    print(new_config)
    driver.config = new_config
    # Wait for write to EEPROM to complete.
    time.sleep_ms(10)
    # Re-initialize according to the new configuration in EEPROM.
    driver.load_config()


disp = M5ili9341()
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=10000)
ui_context = ui.ui_context(disp, i2c)
gc.collect()


async def faces_encoder_update(encoder):
    while True:
        encoder.update()
        await asyncio.sleep_ms(10)
        

async def flash_leds(encoder, pulse_duration_ms=25, wait_duration_ms=1000):
    while True:
        for i in range(3):
            for index in range(10):
                encoder.set_led(index, (255 if i == 0 else 0,
                                        255 if i == 1 else 0,
                                        255 if i == 2 else 0))
                gc.collect()
                await asyncio.sleep_ms(pulse_duration_ms)

        for index in range(12):
            encoder.set_led(index, (0, 0, 0))
            gc.collect()
            await asyncio.sleep_ms(pulse_duration_ms)
        await asyncio.sleep_ms(wait_duration_ms)

encoder = ui_context['faces_driver'].encoder

loop = asyncio.get_event_loop()
loop.create_task(faces_encoder_update(encoder))

tabview = InputsTabView(lv.scr_act(), (ui_context['button_driver'],
                                       ui_context['faces_driver']))


# # Configuration

# For each pump and valve:
#  - `addr`: I2C address of corresponding Grove motor control board
#  - `index`: output index (0-3) within the Grove motor control board
pumps = OrderedDict([('16-3', {'addr': 16, 'index': 2}),
                     ('16-4', {'addr': 16, 'index': 3}),
                     ('17-1', {'addr': 17, 'index': 0}),
                     ('17-2', {'addr': 17, 'index': 1}),
                     ('17-3', {'addr': 17, 'index': 2}),
                     ('17-4', {'addr': 17, 'index': 3}),
                     ('18-1', {'addr': 18, 'index': 0}),
                     ('18-2', {'addr': 18, 'index': 1}),
                     ('18-3', {'addr': 18, 'index': 2}),
                     ('18-4', {'addr': 18, 'index': 3})])
    
valves = OrderedDict([('15-1', {'addr': 15, 'index': 0}),
                      ('15-2', {'addr': 15, 'index': 1}),
                      ('15-3', {'addr': 15, 'index': 2}),
                      ('15-4', {'addr': 15, 'index': 3}),
                      ('16-1', {'addr': 16, 'index': 0}),
                      ('16-2', {'addr': 16, 'index': 1})])

pump_list = tabview.add_widget('Pumps', ui.PumpList, pumps.keys(),
                               ui_context['style'])
valve_list = tabview.add_widget('Valves', ui.ValveList, valves.keys(),
                                ui_context['style'])
gc.collect()

def pump_callback(i2c, i2c_address, pin, pump_i, obj, event, *args, **kwargs):
    loop = asyncio.get_event_loop()
    if event == lv.EVENT.PRESSED:
        period_ms = int(1e3 * pump_i.period)
        off_ms = max(max(period_ms, 50) - 50, 150)
        loop.create_task(pump(i2c, i2c_address, pin, pump_i.pulses,
                              off_ms=off_ms, **kwargs))
        
output_pins = (gm.IN1, gm.IN2, gm.IN3, gm.IN4)
for config_i, pump_i in zip(pumps.values(), pump_list.pumps):
    pump_i.button.set_event_cb(ft.partial(pump_callback, i2c, config_i['addr'],
                                          output_pins[config_i['index']],
                                          pump_i))
gc.collect()

def valve_callback(i2c, i2c_address, pin, obj, event, *args, **kwargs):
    loop = asyncio.get_event_loop()
    if event == lv.EVENT.VALUE_CHANGED:
        loop.create_task(set_valve(i2c, i2c_address, pin, obj.get_state(), **kwargs))

gc.collect()
        
for config_i, valve_i in zip(valves.values(), valve_list.valves):
    valve_i.switch.set_event_cb(ft.partial(valve_callback, i2c, config_i['addr'],
                                           output_pins[config_i['index']]))
gc.collect()

_thread.start_new_thread(loop.run_forever, tuple())
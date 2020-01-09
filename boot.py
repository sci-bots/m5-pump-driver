import _thread
import gc
import sys
sys.path.insert(0, '/_lib')  # pragma: no cover
import time
import uasyncio as asyncio

from base_node import BaseDriver, replace
from config import DEFAULT_SETTINGS, address_map, steps
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

pumps = sorted(set(pump for super_step in steps for step in super_step['steps']
                   for pump in (step['pump'] if isinstance(step['pump'], list)
                                else [step['pump']])))
valves = sorted(set(valve['valve'] for super_step in steps
                    for step in super_step['steps']
                    for valve in step.get('valves', tuple())))

step_names = tuple(step['label'] for super_step in steps
                   for step in super_step['steps'])
steps_list = tabview.add_widget('Steps', ui.PumpList, step_names,
                                ui_context['style'])
pump_list = tabview.add_widget('Pumps', ui.PumpList, pumps,
                               ui_context['style'])
valve_list = tabview.add_widget('Valves', ui.ValveList, valves,
                                ui_context['style'])
gc.collect()

def pump_callback(i2c, i2c_address, pin, pump_i, obj, event, *args, **kwargs):
    loop = asyncio.get_event_loop()
    if event == lv.EVENT.PRESSED:
        period_ms = int(1e3 * pump_i.period)
        off_ms = max(max(period_ms, 50) - 50, 150)
        loop.create_task(pump(i2c, i2c_address, pin, pump_i.pulses,
                              off_ms=off_ms))
        
output_pins = (gm.IN1, gm.IN2, gm.IN3, gm.IN4)
for config_i, pump_i in zip((address_map[p] for p in pumps), pump_list.pumps):
    pump_i.button.set_event_cb(ft.partial(pump_callback, i2c, config_i['addr'],
                                          output_pins[config_i['index']],
                                          pump_i))
    gc.collect()

def valve_callback(i2c, i2c_address, pin, obj, event, *args, **kwargs):
    loop = asyncio.get_event_loop()
    if event == lv.EVENT.VALUE_CHANGED:
        loop.create_task(set_valve(i2c, i2c_address, pin, obj.get_state()))

gc.collect()
        
for config_i, valve_i in zip((address_map[v] for v in valves),
                             valve_list.valves):
    valve_i.switch.set_event_cb(ft.partial(valve_callback, i2c,
                                           config_i['addr'],
                                           output_pins[config_i['index']]))
    gc.collect()

def apply_step(step, widget):
    loop = asyncio.get_event_loop()
    if 'valves' in step:
        for valve_state in step['valves']:
            config = address_map[valve_state['valve']]
            loop.create_task(set_valve(i2c, config['addr'],
                                       output_pins[config['index']],
                                       valve_state['path']))

    if 'pump' in step:
        pumps = (step['pump'] if isinstance(step['pump'], list)
                 else [step['pump']])
        for key in pumps:
            p = address_map[key]
            period_ms = int(1e3 * widget.period)
            off_ms = max(max(period_ms, 50) - 50, 150)
            loop.create_task(pump(i2c, p['addr'], output_pins[p['index']],
                                  widget.pulses, off_ms=off_ms))

def step_callback(step, widget, obj, event, *args, **kwargs):
    if event == lv.EVENT.PRESSED:
        apply_step(step, widget)
        gc.collect()

for step_i, widget_i in zip((step for super_step in steps
                             for step in super_step['steps']),
                            steps_list.pumps):
    widget_i.button.set_event_cb(ft.partial(step_callback, step_i, widget_i))
    gc.collect()


_thread.start_new_thread(loop.run_forever, tuple())
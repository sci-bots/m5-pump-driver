import _thread
import gc
import sys
sys.path.insert(0, '/_lib')  # pragma: no cover
import time
import uasyncio as asyncio
import math

from base_node import BaseDriver, replace
from config import DEFAULT_SETTINGS, address_map, steps
from machine import I2C, Pin
from lvgl_helpers import InputsTabView
from m5_lvgl import M5ili9341
from pump import Pump
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

switches = sorted(set(switches['pin'] for super_step in steps
                    for step in super_step['steps']
                    for switches in step.get('switches', tuple())))
step_names = tuple(step['label'] for super_step in steps
                   for step in super_step['steps'])
steps_tab = tabview.add_widget('Steps', ui.StepList, step_names,
                               ui_context['style'])
steps_list = [step for super_step in steps for step in super_step['steps']]

sequences_tab = tabview.add_widget('Sequences', ui.SequenceList, ['Mix A+B'],
                                   ui_context['style'])

gc.collect()

running_pumps = {}
mix_ab_running = False
mix_ab_start_time = 0

async def mix_ab():
    global mix_ab_running
    global mix_ab_start_time

    sequence = sequences_tab.sequences[0]
    liquid_in_a = True

    while True:
        if mix_ab_running:
            run_time = time.time() - mix_ab_start_time
            
            seconds = run_time % 60
            minutes = math.floor(run_time % 3600 / 60)
            hours = math.floor(run_time / 3600)

            sequence.time.set_text('%02d:%02d:%02d' % (hours, minutes, seconds))

            if minutes == 0 and liquid_in_a:
                i = find_step('A -> B')
                apply_step(steps_list[i], steps_tab.steps[i])
                liquid_in_a = False
            elif minutes == 30 and not liquid_in_a:
                i = find_step('B -> A')
                apply_step(steps_list[i], steps_tab.steps[i])
                liquid_in_a = True

            if hours >= 16:
                sequence.switch.off(0)
                mix_ab_callback(sequence.switch, lv.EVENT.VALUE_CHANGED)

        await asyncio.sleep(1)


def find_step(name):
    for i, name_i in zip(range(len(step_names)), step_names):
        if name_i == name:
            return i


def mix_ab_callback(obj, event, *args, **kwargs):
    global mix_ab_running
    global mix_ab_start_time

    if event == lv.EVENT.VALUE_CHANGED:
        if obj.get_state():
            mix_ab_running = True
            mix_ab_start_time = time.time()
        else:
            mix_ab_running = False
            sequences_tab.sequences[0].time.set_text('')


sequences_tab.sequences[0].switch.set_event_cb(mix_ab_callback)

loop.create_task(mix_ab())

gc.collect()

output_pins = (gm.IN1, gm.IN2, gm.IN3, gm.IN4)

async def set_switch(pin, value):
    Pin(pin, Pin.OUT).value(value)
    gc.collect()


def cleanup_pumps():
    global running_pumps
    for k, v in running_pumps.items():
        if v.pulses == 0:
            i = find_step(k)
            if steps_tab.steps[i].button.get_state():
                steps_tab.steps[i].button.toggle()
            running_pumps.pop(k)
    gc.collect()


def apply_step(step, widget):
    global running_pumps
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

            # If this step is currently running, kill it
            if step['label'] in running_pumps:
                running_pumps[step['label']].stop()

            running_pumps[step['label']] = Pump(i2c, p['addr'],
                output_pins[p['index']], cleanup_pumps, off_ms)
            loop.create_task(running_pumps[step['label']].execute(widget.pulses))

    if 'switches' in step:
        for switch_state in step['switches']:
            loop.create_task(set_switch(switch_state['pin'],
                                        switch_state['value']))

def step_callback(step, widget, obj, event, *args, **kwargs):
    global running_pumps
    if event == lv.EVENT.VALUE_CHANGED:
        state = widget.button.get_state()

        # button toggled on
        if state == lv.btn.STATE.TGL_REL:
            apply_step(step, widget)
        # button toggled off
        elif state == lv.btn.STATE.REL:
            if step['label'] in running_pumps:
                running_pumps[step['label']].stop()
        gc.collect()

for step_i, widget_i in zip((step for super_step in steps
                             for step in super_step['steps']),
                            steps_tab.steps):
    widget_i.button.set_event_cb(ft.partial(step_callback, step_i, widget_i))
    gc.collect()

    # Update the number of 'pulses' for steps where it is specified.
    if 'pulses' in step_i.keys():
        widget_i.pulses_spinbox.set_value(step_i['pulses'])
        gc.collect()

# Cycle the encoder through all of the widgets on the "Steps" tab to hide
# the blinking cursors on the spinboxes.
encoder._diff = len(steps_tab.steps) * 3 + 1

_thread.start_new_thread(loop.run_forever, tuple())
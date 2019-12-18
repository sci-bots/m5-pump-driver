import gc
import sys

from m5_lvgl import (ButtonsInputEncoder, FacesEncoderInputEncoder,
                     EncoderInputDriver)
from lvgl_helpers import InputsContainer
import lvgl as lv


class Button(lv.btn):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.label = lv.label(self)
        self.label.set_text(text)
        self.set_fit(lv.FIT.TIGHT)


class Pump(lv.cont):
    def __init__(
            self, parent, label, default_pulses=20, min_pulses=1,
            max_pulses=125, style=None):
        super().__init__(parent)
        if style is None:
            style = lv.style_t()
            lv.style_copy(style, lv.style_transp)
        self.set_style(lv.cont.STYLE.MAIN, style)
        self.set_auto_realign(True)
        self.set_fit(lv.FIT.TIGHT)
        self.set_layout(lv.LAYOUT.ROW_M)

        button_i = Button(self, label)

        pulses_i = lv.cont(self)
        pulses_i.set_style(lv.cont.STYLE.MAIN, style)
        pulses_i.set_auto_realign(True)
        pulses_i.set_fit(lv.FIT.TIGHT)
        pulses_i.set_layout(lv.LAYOUT.ROW_M)
        pulses_label_i = lv.label(pulses_i)
        pulses_label_i.set_text('Pulses')
        pulses_spinbox = lv.spinbox(pulses_i)
        character_width = 10
        digits = 3
        pulses_spinbox.set_width((digits + 1) * character_width)
        pulses_spinbox.set_digit_format(digits, 0)
        pulses_spinbox.set_range(1, 125)
        pulses_spinbox.set_value(20)

        period_i = lv.cont(self)
        period_i.set_style(lv.cont.STYLE.MAIN, style)
        period_i.set_auto_realign(True)
        period_i.set_fit(lv.FIT.TIGHT)
        period_i.set_layout(lv.LAYOUT.ROW_M)
        period_label_i = lv.label(period_i)
        period_label_i.set_text('Period (s)')
        period_spinbox = lv.spinbox(period_i)
        period_spinbox.set_width((digits + 1) * character_width)
        period_spinbox.set_digit_format(digits, digits - 1)
        period_spinbox.set_range(2, 1000)
        period_spinbox.set_value(5)

        self.button = button_i
        self.pulses_spinbox = pulses_spinbox
        self.period_spinbox = period_spinbox

    @property
    def pulses(self):
        return self.pulses_spinbox.get_value()

    @property
    def period(self):
        return self.period_spinbox.get_value() * .1

    def children(self):
        return [self.button, self.pulses_spinbox, self.period_spinbox]


class PumpWindow(lv.win):
    def __init__(self, parent, style=None):
        super().__init__(parent)
        if style is None:
            style = lv.style_t()
            lv.style_copy(style, lv.style_transp)
        self.set_style(lv.win.STYLE.CONTENT, style)
        self.group = lv.group_create()
        self.close_btn = self.add_btn(lv.SYMBOL.CLOSE)
        lv.group_add_obj(self.group, self.close_btn)
        self.close_btn.set_event_cb(lv.win.close_event_cb)

        # Automatically scroll view to show focused object.
        def group_focus_cb(group):
            f = lv.group_get_focused(self.group)
            if f != self:
                self.focus(f, lv.ANIM.ON)

        lv.group_set_focus_cb(self.group, group_focus_cb)

        content = self.get_content()
        lv.page.set_scrl_layout(content, lv.LAYOUT.COL_L)

        self.pumps = [Pump(content, 'Pump obj %d' % i, style=style)
                      for i in range(2)]
        # for pump_i in self.pumps:
        #     for child_ij in pump_i.children():
        #         lv.group_add_obj(self.group, child_ij)
        for child_i in reversed(list(children_recursive(content))):
            if not isinstance(child_i, (lv.obj, lv.cont, lv.label)):
                lv.group_add_obj(self.group, child_i)



def ui_context(disp, i2c):
    # disp = M5ili9341()

    button_encoder = ButtonsInputEncoder()
    button_driver = EncoderInputDriver(button_encoder)

    faces_encoder = FacesEncoderInputEncoder(i2c)
    faces_driver = EncoderInputDriver(faces_encoder)

    scr = lv.obj()
    win_style = lv.style_t()
    lv.style_copy(win_style, lv.style_transp)
    win_style.body.padding.left = 5
    win_style.body.padding.right = 5
    win_style.body.padding.top = 0
    win_style.body.padding.bottom = 0
    win_style.body.padding.inner = 0

    lv.scr_load(scr)

    ui_context_ = {'scr': scr, 'style': win_style,
                   'button_driver': button_driver,
                   'faces_driver': faces_driver}
    return ui_context_


class PumpList(InputsContainer):
    def __init__(self, parent, names, style=None):
        super().__init__(parent, style=style)
        self.pumps = [Pump(self, name, style=style)
                      for name in names]


class Valve(lv.cont):
    def __init__(self, parent, label, style=None):
        super().__init__(parent)
        if style is None:
            style = lv.style_t()
            lv.style_copy(style, lv.style_transp)
        self.set_style(lv.cont.STYLE.MAIN, style)
        self.set_auto_realign(True)
        self.set_fit(lv.FIT.TIGHT)
        self.set_layout(lv.LAYOUT.ROW_M)

        self.label = lv.label(self)
        self.label.set_text(label)
        self.switch = lv.sw(self)
        

class ValveList(InputsContainer):
    def __init__(self, parent, names, style=None):
        super().__init__(parent, style=style)
        self.valves = [Valve(self, name, style=style)
                       for name in names]
        self.set_layout(lv.LAYOUT.PRETTY)
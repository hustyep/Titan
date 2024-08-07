import tkinter as tk
from src.gui.interfaces import LabelFrame, Frame
from src.common.interfaces import Configurable
from src.common import utils, bot_status
import keyboard
import time
import threading
from src.common import bot_action


class Shadower(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Shadower', **kwargs)

        self.settings = ShadowerMacrosSettings('macros_shadower')

        row = Frame(self)
        row.pack(side=tk.TOP, expand=True, pady=5, padx=5)

        index = 0
        self.check_boxes = []
        self.check_values = []
        for k, v in self.settings.config.items():
            value = tk.BooleanVar(value=v)
            check = tk.Checkbutton(
                row,
                variable=value,
                text=k,
                command=lambda type=k: self._on_change(type)
            )
            check.grid(row=index // 2, column=index %
                       2, sticky=tk.W, padx=(index % 2) * 50)
            index += 1
            self.check_boxes.append(check)
            self.check_values.append(value)
            if v:
                self._on_change(k)

    def _on_change(self, type):
        for i in range(len(self.check_boxes)):
            check = self.check_boxes[i]
            value = self.check_values[i]
            self.settings.set(check.cget('text'), value.get())
        self.settings.save_config()

        value = self.settings.get(type)
        hotkey = None
        target = None
        match (type):
            case 'Meso Explosion':
                hotkey = ['f', 'v']
                target = self.meso_explosion
            case 'Trickblade':
                hotkey = ['a']
                target = self.trickblade

        if hotkey:
            if value:
                for key in hotkey:
                    keyboard.on_press_key(key, target)
                # keyboard.add_hotkey(hotkey, target)
            else:
                # keyboard.remove_hotkey(hotkey)
                keyboard.unhook_key(hotkey)

    def meso_explosion(self, event):
        threading.Timer(0.1, bot_action.click_key, ('d', )).start()

    @bot_status.run_if_disabled
    def trickblade(self) -> None:
        bot_action.click_key('v')
        bot_action.click_key('a')


class ShadowerMacrosSettings(Configurable):
    DEFAULT_CONFIG = {
        'Meso Explosion': False,
        'Trickblade': False,
    }

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        assert key in self.config
        self.config[key] = value

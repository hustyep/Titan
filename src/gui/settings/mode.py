import tkinter as tk
from src.gui.interfaces import LabelFrame, Frame
from src.common.gui_setting import gui_setting

from src.common.constants import BotRunMode

class Mode(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'mode', **kwargs)

        self.setting = gui_setting.mode
        self.mode = tk.StringVar(value=self.setting.type.value)

        mode_row = Frame(self)
        mode_row.pack(side=tk.TOP, fill='x', expand=True, pady=(0, 5), padx=5)
        radio_group = Frame(mode_row)
        radio_group.pack(side=tk.TOP)
        
        for type in BotRunMode:
            radio = tk.Radiobutton(
                radio_group,
                text=type.value,
                variable=self.mode,
                value=type.value,
                command=self._on_change
            )
            radio.pack(side=tk.LEFT, padx=(0, 10))

    def _on_change(self):
        self.setting.type = self.mode.get()
        self.setting.save_config()

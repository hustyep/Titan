import tkinter as tk
from src.gui.interfaces import LabelFrame, Frame
from src.common import bot_settings
from src.common.gui_setting import gui_setting

class Auto(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Auto', **kwargs)

        self.settings = gui_setting.auto

        row = Frame(self)
        row.pack(side=tk.TOP, expand=True, pady=5, padx=5)

        index = 0
        self.check_boxes = []
        self.check_values = []
        for k, v in self.settings.config.items():
            if k == 'Channel':
                continue
            try:
                value = tk.BooleanVar(value=v)
            except Exception as e:
                value = tk.BooleanVar(value=False)
            check = tk.Checkbutton(
                row,
                variable=value,
                text=k,
                command=self._on_change
            )
            check.grid(row=0, column=index, sticky=tk.W, padx=10)
            index += 1
            self.check_boxes.append(check)
            self.check_values.append(value)
            
        channel_row = Frame(self)
        channel_row.pack(side=tk.TOP, expand=True, pady=5, padx=5)
        
        label = tk.Label(channel_row, text='Auto login channel:')
        label.pack(side=tk.LEFT, padx=(0, 5), fill='x')
        
        self.display_var = tk.IntVar(value=0)
        self.display_var.trace('w', self._on_channel_changed)
        self.channel_entry = tk.Entry(channel_row,
                         validate='key',
                         textvariable = self.display_var,
                         width=15,
                         takefocus=False)
        self.channel_entry.pack(side=tk.LEFT, padx=(15, 5))

    def _on_change(self):
        for i in range(len(self.check_boxes)):
            check = self.check_boxes[i]
            value = self.check_values[i]
            self.settings.set(check.cget('text'), value.get())
        self.settings.save_config()        

    def _on_channel_changed(self):
        value = self.display_var.get()
        self.settings.set('Channel', value)
        self.settings.save_config()

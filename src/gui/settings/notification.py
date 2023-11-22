import tkinter as tk
from src.gui.interfaces import LabelFrame, Frame
from src.common.gui_setting import gui_setting
from src.common import bot_status


class Notification(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Notification', **kwargs)

        self.notification_settings = gui_setting.notification
        self.notice_level = tk.IntVar(
            value=self.notification_settings.get('notice_level'))
        self.notice_levels = ['Fatal', 'Error', 'Warnning', 'Info', 'Debug']
        bot_status.notice_level = int(self.notice_level.get())

        channel_row = Frame(self)
        channel_row.pack(side=tk.TOP, expand=True, pady=5, padx=5)

        index = 0
        self.check_boxes = []
        self.check_values = []
        for k, v in self.notification_settings.config.items():
            try:
                value = tk.BooleanVar(value=v)
            except Exception as e:
                value = tk.BooleanVar(value=False)
            check = tk.Checkbutton(
                channel_row,
                variable=value,
                text=k,
                command=self._on_change
            )
            check.grid(row=1, column=index, sticky=tk.W,
                       padx=15 if index > 0 else 0)
            self.check_boxes.append(check)
            self.check_values.append(value)
            index += 1
            if index == 4:
                break

        level_row = Frame(self)
        level_row.pack(side=tk.TOP, fill='x', expand=True, pady=(0, 5), padx=5)
        label = tk.Label(level_row, text='Level:')
        label.pack(side=tk.LEFT, padx=(0, 0))
        radio_group = Frame(level_row)
        radio_group.pack(side=tk.LEFT)
        for i in range(1, 6):
            radio = tk.Radiobutton(
                radio_group,
                text=self.notice_levels[i-1],
                variable=self.notice_level,
                value=i,
                command=self._on_change
            )
            radio.pack(side=tk.LEFT, padx=(5, 0))

    def _on_change(self):
        for i in range(len(self.check_boxes)):
            check = self.check_boxes[i]
            value = self.check_values[i]
            self.notification_settings.set(check.cget('text'), value.get())
        self.notification_settings.set("notice_level", self.notice_level.get())
        self.notification_settings.save_config()

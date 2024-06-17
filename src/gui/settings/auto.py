import tkinter as tk
from enum import Enum
from src.gui.interfaces import LabelFrame, Frame
from src.common import bot_status
from src.common.gui_setting import gui_setting
from src.common import utils
from src.common.image_template import *
from src.modules.capture import capture
import keyboard
from src.common.hid import hid
import time
import threading
from src.chat_bot.chat_bot import chat_bot

class PotentialType(Enum):
    MOB = 'mob'
    ATT = 'att'
    LUK = 'luck'
    STR = 'str'
    CD = 'critical damege'

class PotentialLevel(Enum):
    HIGH = 200
    LOW = 160

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
        
        self.display_var = tk.IntVar(value=self.settings.get('Channel'))
        self.display_var.trace('w', self._on_channel_changed)
        self.channel_entry = tk.Entry(channel_row,
                         validate='key',
                         textvariable = self.display_var,
                         width=15,
                         takefocus=False)
        self.channel_entry.pack(side=tk.LEFT, padx=(15, 5))
        
        keyboard.on_press_key('f3', self.on_flame)


    def _on_change(self):
        for i in range(len(self.check_boxes)):
            check = self.check_boxes[i]
            value = self.check_values[i]
            self.settings.set(check.cget('text'), value.get())
        self.settings.save_config()        

    def _on_channel_changed(self, a, b, c):
        value = self.display_var.get()
        self.settings.set('Channel', value)
        self.settings.save_config()
        
    @bot_status.run_if_disabled('')
    def on_flame(self, event):
        if not gui_setting.auto.cube:
            return
        if bot_status.cubing:
            self._stop_flame()
        else:
            threading.Thread(target=self._start_flame,).start()

    @bot_status.run_if_disabled('')
    def _start_flame(self):
        print("Start Flame>>>>>>>>>>>")
        bot_status.cubing = True
        
        width = 100
        height = 80
        frame = capture.frame
        matchs = utils.multi_match(frame, POTENTIAL_RESULT_TEMPLATE, threshold=0.8, debug=False)
        if matchs:
            pos = matchs[0]
            x = pos[0] - 28
            y = pos[1] + 12
        else:
            self._stop_flame()
            return
        
        rect = (x, y, width, height)
        while bot_status.cubing:
            if self._flame_result(rect):
                self._stop_flame()
                chat_bot.voice_call()
                break
            else:
                time.sleep(1)
                self._flame_onemore(rect)
                
    @bot_status.run_if_disabled('')
    def _flame_result(self, rect, target=120):
        x, y, width, height = rect
        while len(utils.multi_match(capture.frame[y+height:y+height+30, x:x+150], ATT_INCREASE_TEMPLATE, threshold=0.95, debug=False)) == 0:
            time.sleep(0.05)
        time.sleep(0.5)
        result_frame = capture.frame[y:y+height, x:x+width]
        
        matchs1 = utils.multi_match(result_frame, LUK_PLUS_TEMPLATE, threshold=0.95, center=False, debug=False)
        matchs2 = utils.multi_match(result_frame, ATT_PLUS_TEMPLATE, threshold=0.95, center=False, debug=False)
        matchs3 = utils.multi_match(result_frame, ALL_PLUS_TEMPLATE, threshold=0.95, center=False, debug=False)
        
        total = 0
        if len(matchs1) > 0:
            x, y = matchs1[0]
            height, width = LUK_PLUS_TEMPLATE.shape

            frame = result_frame[max(0, y-5): y+height+5,]
            text = utils.image_2_str(frame).replace('\n', '').replace('.', '')
            num = text.split('+')[1].replace(',', '').replace('.', '')
            total += int(num)
            print(f'LUK: {int(num)}')
            
        if len(matchs2) > 0:
            x, y = matchs2[0]
            height, width = ATT_PLUS_TEMPLATE.shape
            frame = result_frame[max(0, y-5): y+height+5,]
            text = utils.image_2_str(frame).replace('\n', '')
            num = text.split('+')[1]
            total += int(num) * 3
            print(f'ATT: {int(num)}')
        if len(matchs3) > 0:
            x, y = matchs3[0]
            height, width = ALL_PLUS_TEMPLATE.shape
            frame = result_frame[max(0, y-5): y+height+5, x+width-3:]
            text = utils.image_2_str(frame)
            total += int(text[0]) * 8
            print(f'ALL: {int(text[0])}%')
                     
        print(f'total={total}')
        return total >= target
        
    @bot_status.run_if_disabled('')
    def _flame_onemore(self, rect):
        if not bot_status.cubing:
            return
        print("Try Again------------------------")
        hid.mouse_left_click()
        time.sleep(0.5)
        for _ in range(0, 4):
            if not bot_status.cubing:
                return
            hid.key_press('enter')
            time.sleep(0.2)
            if not bot_status.cubing:
                return
            
        x, y, width, height = rect
        start = time.time()
        while len(utils.multi_match(capture.frame[y:y+30, x:x+150], ATT_INCREASE_TEMPLATE, threshold=0.95, debug=False)) > 0:
            if not bot_status.cubing:
                break
            time.sleep(0.05)
            if time.time() - start > 5:
                break
            if not bot_status.cubing:
                break
        
    @bot_status.run_if_disabled('')
    def _stop_flame(self):
        print("Stop Flame>>>>>>>>>>>>>>>")
        bot_status.cubing = False
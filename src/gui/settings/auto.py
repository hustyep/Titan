import tkinter as tk
from enum import Enum
from src.gui.interfaces import LabelFrame, Frame
from src.common import bot_status
from src.common.gui_setting import gui_setting
from src.common import utils
from src.common.image_template import *
from src.modules.capture import capture
from src.common.action_simulator import ActionSimulator
import keyboard
from src.common.hid import hid
import time
import threading

class PotentialType(Enum):
    ATT = 'att'
    LUK = 'luck'

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
        
        keyboard.on_press_key('f2', self.on_cube)


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
    def on_cube(self, event):
        if not gui_setting.auto.cube:
            return
        if bot_status.cubing:
            self._stop_cube()
        else:
            threading.Thread(target=self._start_cube,).start()
            
    @bot_status.run_if_disabled('')
    def _start_cube(self):
        print("_start_cube")
        bot_status.cubing = True
        
        width = 90
        height = 44
        frame = capture.frame
        matchs1 = utils.multi_match(frame, POTENTIAL_RESULT_TEMPLATE, threshold=0.8, debug=False)
        matchs2 = utils.multi_match(frame, POTENTIAL_AFTER_TEMPLATE, threshold=0.95, debug=False)
        if matchs1:
            pos = matchs1[0]
            x = pos[0] - 23
            y = pos[1] + 23
        elif matchs2:
            pos = matchs2[0]
            x = pos[0] - 23
            y = pos[1] + 23
        else:
            self._stop_cube()
            return
        
        rect = (x, y, width, height)
        while bot_status.cubing:
            if self._cube_result(rect, PotentialType.LUK, PotentialLevel.LOW):
                self._stop_cube()
                break
            else:
                self._cube_onemore(rect)
            
    @bot_status.run_if_disabled('')
    def _stop_cube(self):
        print("_stop_cube")
        bot_status.cubing = False
    
    @bot_status.run_if_disabled('')
    def _cube_result(self, rect, type: PotentialType, level: PotentialLevel):
        x, y, width, height = rect

        while len(utils.multi_match(capture.frame[y-20:y+5, x:x+150], POTENTIAL_LEGENDARY_TEMPLATE, threshold=0.95, debug=False)) == 0:
            time.sleep(0.05)
        time.sleep(1)
        result_frame = capture.frame[y:y+height, x:x+width]
        
        if type == PotentialType.ATT:
            if level == PotentialLevel.HIGH:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_ATT10_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_ATT13_TEMPLATE, threshold=0.95, debug=False)
                print(f"cube_result:\natt10*{len(matchs1)}\natt13*{len(matchs2)}")
            else:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_ATT9_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_ATT12_TEMPLATE, threshold=0.95, debug=False)
                print(f"cube_result:\natt9*{len(matchs1)}\natt12*{len(matchs2)}")
            if len(matchs1) + len(matchs2) >= 2:
                return True
            else:
                return False
        else:
            if level == PotentialLevel.HIGH:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_LUK13_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_LUK10_TEMPLATE, threshold=0.95, debug=False)
                matchs3 = utils.multi_match(result_frame, POTENTIAL_ALL10_TEMPLATE, threshold=0.95, debug=False)
                matchs4 = utils.multi_match(result_frame, POTENTIAL_ALL7_TEMPLATE, threshold=0.95, debug=False)
                print(f"cube_result:\nLUK13*{len(matchs1)}\nLUK10*{len(matchs2)}\nALL10*{len(matchs3)}\nALL7*{len(matchs4)}")
                total = len(matchs1) * 13 + len(matchs2) * 10 + len(matchs3) * 10 + len(matchs4) * 7
                print(f"total={total}")
                if total >= 33:
                    return True
                else:
                    return False
            else:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_LUK12_TEMPLATE, threshold=0.95, debug=True)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_LUK9_TEMPLATE, threshold=0.95, debug=False)
                matchs3 = utils.multi_match(result_frame, POTENTIAL_ALL9_TEMPLATE, threshold=0.95, debug=False)
                matchs4 = utils.multi_match(result_frame, POTENTIAL_ALL6_TEMPLATE, threshold=0.95, debug=False)
                print(f"cube_result:\nLUK12*{len(matchs1)}\nLUK9*{len(matchs2)}\nALL9*{len(matchs3)}\nALL6*{len(matchs4)}")
                total = len(matchs1) * 12 + len(matchs2) * 9 + len(matchs3) * 9 + len(matchs4) * 6
                print(f"total={total}")
                if total >= 30:
                    return True
                else:
                    return False
    
    @bot_status.run_if_disabled('')
    def _cube_onemore(self, rect):
        print("_cube_onemore")
        hid.mouse_left_click()
        time.sleep(0.5)
        for _ in range(0, 4):
            hid.key_press('enter')
            time.sleep(0.2)
            
        x, y, width, height = rect
        start = time.time()
        while len(utils.multi_match(capture.frame[y-20:y+5, x:x+150], POTENTIAL_LEGENDARY_TEMPLATE, threshold=0.95, debug=False)) > 0:
            time.sleep(0.05)
            if time.time() - start > 5:
                break
        
        
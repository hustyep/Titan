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
from src.modules.chat_bot import chat_bot

class PotentialType(Enum):
    MOB = 'mob'
    ATT = 'att'
    LUK = 'luck'
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
        
        keyboard.on_press_key('f2', self.on_cube)
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
            x = pos[0] - 20
            y = pos[1] + 23
        else:
            self._stop_cube()
            return
        
        rect = (x, y, width, height)
        while bot_status.cubing:
            if self._cube_result(rect, PotentialType.MOB, PotentialLevel.HIGH):
                self._stop_cube()
                chat_bot.voice_call()
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
            if len(matchs1) + len(matchs2) >= 3:
                return True
            else:
                return False
        elif type == PotentialType.LUK:
            if level == PotentialLevel.HIGH:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_LUK13_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_LUK10_TEMPLATE, threshold=0.95, debug=False)
                matchs3 = utils.multi_match(result_frame, POTENTIAL_ALL10_TEMPLATE, threshold=0.95, debug=False)
                matchs4 = utils.multi_match(result_frame, POTENTIAL_ALL7_TEMPLATE, threshold=0.95, debug=False)
                print(f"cube_result:\nLUK13*{len(matchs1)}\nLUK10*{len(matchs2)}\nALL10*{len(matchs3)}\nALL7*{len(matchs4)}")
                total = len(matchs1) * 13 + len(matchs2) * 10 + len(matchs3) * 10 + len(matchs4) * 7
                print(f"total={total}")
                if total >= 30:
                    return True
                else:
                    return False
            else:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_LUK12_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_LUK9_TEMPLATE, threshold=0.95, debug=False)
                matchs3 = utils.multi_match(result_frame, POTENTIAL_ALL9_TEMPLATE, threshold=0.96, debug=False)
                matchs4 = utils.multi_match(result_frame, POTENTIAL_ALL6_TEMPLATE, threshold=0.96, debug=False)
                total = len(matchs1) * 12 + len(matchs2) * 9 + len(matchs3) * 9 + len(matchs4) * 6
                print(f"cube_result:\nLUK12*{len(matchs1)}\nLUK9*{len(matchs2)}\nALL9*{len(matchs3)}\nALL6*{len(matchs4)}")
                print(f"total={total}")
                if total >= 30:
                    return True
                else:
                    return False
        elif type == PotentialType.CD:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_CD8_TEMPLATE, threshold=0.9, debug=False)
                print(f"cd:{len(matchs1)}")
                if len(matchs1) >= 2:
                    return True
                else:
                    return False
        else:
            matchs1 = utils.multi_match(result_frame, POTENTIAL_MESOS_TEMPLATE, threshold=0.9, debug=False)
            matchs2 = utils.multi_match(result_frame, POTENTIAL_DROP_TEMPLATE, threshold=0.9, debug=False)
            total = len(matchs1) + len(matchs2)
            print(f"cube_result:\nmeso*{len(matchs1)}\ndrop*{len(matchs2)}")
            print(f"total={total}")
            if total >= 2:
                return True
            
            if level == PotentialLevel.HIGH:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_LUK13_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_LUK10_TEMPLATE, threshold=0.95, debug=False)
                matchs3 = utils.multi_match(result_frame, POTENTIAL_ALL10_TEMPLATE, threshold=0.95, debug=False)
                matchs4 = utils.multi_match(result_frame, POTENTIAL_ALL7_TEMPLATE, threshold=0.95, debug=False)
                total = len(matchs1) * 13 + len(matchs2) * 10 + len(matchs3) * 10 + len(matchs4) * 7
                print(f"cube_result:\nLUK13*{len(matchs1)}\nLUK10*{len(matchs2)}\nALL10*{len(matchs3)}\nALL7*{len(matchs4)}")
                print(f"total={total}")
                if total >= 33:
                    return True
                else:
                    return False
            else:
                matchs1 = utils.multi_match(result_frame, POTENTIAL_LUK12_TEMPLATE, threshold=0.95, debug=False)
                matchs2 = utils.multi_match(result_frame, POTENTIAL_LUK9_TEMPLATE, threshold=0.95, debug=False)
                matchs3 = utils.multi_match(result_frame, POTENTIAL_ALL9_TEMPLATE, threshold=0.96, debug=False)
                matchs4 = utils.multi_match(result_frame, POTENTIAL_ALL6_TEMPLATE, threshold=0.96, debug=False)
                total = len(matchs1) * 12 + len(matchs2) * 9 + len(matchs3) * 9 + len(matchs4) * 6
                print(f"cube_result:\nLUK12*{len(matchs1)}\nLUK9*{len(matchs2)}\nALL9*{len(matchs3)}\nALL6*{len(matchs4)}")
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
        # utils.show_image(capture.frame[y+height:y+height+30, x:x+150])
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
            # try:
            #     frame = result_frame[max(0, y-6): y+height+5, x+width-2:]
            #     text = utils.image_2_str(frame)
            #     total += int(text)
            #     print(f'LUK: {int(text)}')
            # except Exception as e:
                # print(e)
            frame = result_frame[max(0, y-5): y+height+5,]
            text = utils.image_2_str(frame).replace('\n', '').replace('.', '')
            num = text.split('+')[1]
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

        # text = utils.image_2_str(result_frame)
        # content = text.replace("\f", "").split("\n")
        # total = 0
        # for item in content:
        #     if item.startswith('LUK'):
        #         num = item.split('+')[1]
        #         total += int(num)
        #         print(f'LUK: {num}')
        #     elif item.startswith('Attack') or item.startswith('Altack') or item.startswith('Atack'):
        #         num = item.s
        # 
        # 
        # 
        # plit('+')[1]
        #         total += int(num) * 3
        #         print(f'ATT: {num}')
        #     elif item.startswith('All Stats'):
        #         num = item.split('+')[1]
        #         total += int(num[0]) * 8
        #         print(f'All Stats: {num}')            
        print(f'total={total}')
        return total >= target
        
        
    @bot_status.run_if_disabled('')
    def _flame_onemore(self, rect):
        print("Try Again------------------------")
        hid.mouse_left_click()
        time.sleep(0.5)
        for _ in range(0, 4):
            hid.key_press('enter')
            time.sleep(0.2)
            
        x, y, width, height = rect
        start = time.time()
        while len(utils.multi_match(capture.frame[y:y+30, x:x+150], ATT_INCREASE_TEMPLATE, threshold=0.95, debug=False)) > 0:
            time.sleep(0.05)
            if time.time() - start > 5:
                break
        
    @bot_status.run_if_disabled('')
    def _stop_flame(self):
        print("Stop Flame>>>>>>>>>>>>>>>")
        bot_status.cubing = False
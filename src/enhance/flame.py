from enum import Enum
import time
import threading
from src.chat_bot.chat_bot import chat_bot
from src.modules.capture import capture
from src.common import utils, bot_status
from src.common.image_template import *
from src.common.constants import *
from src.common.gui_setting import gui_setting
from src.models.role_model import RoleModel
from src.common.vkeys import *

class Flame:
    def __init__(self):
        self.running = False
        self.role = None
        self.target = 120
    
    def start(self, role: RoleModel):
        if role is None:
            return
        if gui_setting.mode.type != BotRunMode.Flame:
            return
        self.role = role
        if not self.running:
            threading.Thread(target=self.__start_flame,).start()

    def stop(self):
        print("Stop Flame <<<<<<<<<<<<<<<")
        self.running = False

    def __start_flame(self):
        print("Start Flame>>>>>>>>>>>")
        
        self.running = True
        width = 100
        height = 80
        frame = capture.frame
        matchs = utils.multi_match(frame, POTENTIAL_RESULT_TEMPLATE, threshold=0.8, debug=False)
        if matchs:
            pos = matchs[0]
            x = pos[0] - 28
            y = pos[1] + 12
        else:
            self.stop()
            return
        
        rect = (x, y, width, height)
        while self.running:
            if self._flame_result(rect):
                self._stop_flame()
                chat_bot.voice_call()
                break
            else:
                time.sleep(1)
                self._flame_onemore(rect)
                
    @bot_status.run_if_disabled('')
    def _flame_result(self, rect):
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
        return total >= self.target
        
    @bot_status.run_if_enabled
    def _flame_onemore(self, rect):
        if not self.running:
            return
        print("Try Again------------------------")
        mouse_click()
        time.sleep(0.5)
        for _ in range(0, 4):
            press_acc('enter', up_time=0.2)
            
        x, y, width, height = rect
        start = time.time()
        while len(utils.multi_match(capture.frame[y:y+30, x:x+150], ATT_INCREASE_TEMPLATE, threshold=0.95, debug=False)) > 0:
            if not self.running:
                break
            time.sleep(0.05)
            if time.time() - start > 5:
                break
            if not self.running:
                break             

FlameManager = Flame()

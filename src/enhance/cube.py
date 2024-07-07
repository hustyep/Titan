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


class PotentialType(Enum):
    MOB = 'mob'
    ATT = 'att'
    STAT = 'stat'
    CD = 'CD'
    CRIT = 'critical damege'


class Cube:
    def __init__(self):
        self.running = False
        self.role: RoleModel

        self.type = PotentialType.MOB
        self.target = 2

    def start(self, role: RoleModel):
        if gui_setting.mode.type != BotRunMode.Cube:
            return
        self.role = role
        if not self.running:
            threading.Thread(target=self.__start_cube,).start()

    def stop(self):
        print("Stop Cube <<<<<<<<<<<<<<<")
        self.running = False
        bot_status.acting = False
        bot_status.enabled = False

    def __start_cube(self):
        print("Start Cube >>>>>>>>>>>>>>")
        self.running = True
        bot_status.acting = True

        width = 150
        height = 44
        frame = capture.frame
        matchs1 = utils.multi_match(
            frame, POTENTIAL_RESULT_TEMPLATE, threshold=0.8, debug=False)   
        matchs2 = utils.multi_match(
            frame, POTENTIAL_AFTER_TEMPLATE, threshold=0.95, debug=False)
        if matchs1: 
            pos = matchs1[0]
            x = pos[0] - 20
            y = pos[1] + 23
        elif matchs2:
            pos = matchs2[0]
            x = pos[0] - 20
            y = pos[1] + 23
        else:
            self.stop()
            return

        rect = (x, y, width, height)
        while self.running:
            if self.__cube_result(rect, self.type) >= self.target:
                self.stop()
                chat_bot.voice_call()
                break
            else:
                print(f"< target: {self.target}")
                self._cube_onemore(rect)

    @bot_status.run_if_enabled
    def __cube_result(self, rect, type: PotentialType):
        x, y, width, height = rect

        while capture.frame is None or not self._find_legendary(capture.frame[y-20:y+5, x:x+150]):
            time.sleep(0.05)
        time.sleep(1)
        result_frame = capture.frame[y:y+height, x:x+width]

        match type:
            case PotentialType.ATT:
                return self._att_result(result_frame, count_boss=True, count_def=False)
            case PotentialType.STAT:
                if self.role is None:
                    self.stop()
                    return 0
                if self._mob_result(result_frame) == 3:
                    return 999
                return self._stat_result(result_frame, self.role.character.main_stat)
            case PotentialType.CD:
                if self._stat_result(result_frame, self.role.character.main_stat) >= 36:
                    return 999
                return self._cd_result(result_frame)
            case PotentialType.MOB:
                return self._mob_result(result_frame)

        return 0

    @bot_status.run_if_enabled
    def _cube_onemore(self, rect):
        print("_cube_onemore")
        mouse_click()   
        time.sleep(0.5)
        for _ in range(0, 4):
            press_acc('enter', up_time=0.2)

        x, y, width, height = rect
        start = time.time()
        while capture.frame is None or len(utils.multi_match(capture.frame[y-20:y+5, x:x+150], POTENTIAL_LEGENDARY_TEMPLATE, threshold=0.95, debug=False)) > 0:
            time.sleep(0.05)
            if time.time() - start > 5:
                break

    def _find_legendary(self, rect):
        return len(utils.multi_match(rect, POTENTIAL_LEGENDARY_TEMPLATE, threshold=0.94, debug=False)) > 0

    def _att_result(self, result_frame, count_boss=False, count_def=False):
        if not count_boss and not count_def:
            source = [
                ('Att13', 13, POTENTIAL_ATT13_TEMPLATE),
                ('Att10', 10, POTENTIAL_ATT10_TEMPLATE),
                ('Att12', 12, POTENTIAL_ATT12_TEMPLATE),
                ('Att9', 9, POTENTIAL_ATT9_TEMPLATE),
            ]
        else:
            source = [
                ('Att13', 1, POTENTIAL_ATT13_TEMPLATE),
                ('Att10', 1, POTENTIAL_ATT10_TEMPLATE),
                ('Att12', 1, POTENTIAL_ATT12_TEMPLATE),
                ('Att9', 1, POTENTIAL_ATT9_TEMPLATE),
            ]
            if count_boss:
                source.append(('Boss40', 1, POTENTIAL_BOSS40_TEMPLATE))
                source.append(('Boss3x', 1, POTENTIAL_BOSS3x_TEMPLATE))

            if count_def:
                source.append(('Def', 1, POTENTIAL_DEF_TEMPLATE))

        return self.__calculate(result_frame, source)

    def _stat_result(self, result_frame, type: MainStatType):
        result = 0
        match type:
            case MainStatType.LUK:
                source = [  
                    ('LUK13', 13, POTENTIAL_LUK13_TEMPLATE),
                    ('LUK10', 10, POTENTIAL_LUK10_TEMPLATE),
                    ('ALL10', 10, POTENTIAL_ALL10_TEMPLATE),
                    ('ALL7', 7, POTENTIAL_ALL7_TEMPLATE),
                    ('LUK12', 12, POTENTIAL_LUK12_TEMPLATE),
                    ('LUK9', 9, POTENTIAL_LUK9_TEMPLATE),
                    ('ALL9', 9, POTENTIAL_ALL9_TEMPLATE),
                    ('ALL6', 6, POTENTIAL_ALL6_TEMPLATE),
                ]
                result = self.__calculate(result_frame, source)
            case MainStatType.STR:
                source = [
                    ('STR13', 13, POTENTIAL_STR13_TEMPLATE),
                    ('STR10', 10, POTENTIAL_STR10_TEMPLATE),
                    ('ALL10', 10, POTENTIAL_ALL10_TEMPLATE),
                    ('ALL7', 7, POTENTIAL_ALL7_TEMPLATE),
                    ('STR12', 12, POTENTIAL_STR12_TEMPLATE),
                    ('STR9', 9, POTENTIAL_STR9_TEMPLATE),
                    ('ALL9', 9, POTENTIAL_ALL9_TEMPLATE),
                    ('ALL6', 6, POTENTIAL_ALL6_TEMPLATE),
                ]
                result = self.__calculate(result_frame, source)
        return result

    def _cd_result(self, result_frame):
        source = [
            ("CD2", 2, POTENTIAL_CD2_TEMPLATE),
            ("CD1", 1, POTENTIAL_CD2_TEMPLATE),
        ]
        return self.__calculate(result_frame, source)

    def _mob_result(self, result_frame):
        source = [
            ("Drop", 1, POTENTIAL_DROP_TEMPLATE),
            ("Meso", 1, POTENTIAL_MESOS_TEMPLATE),
        ]
        return self.__calculate(result_frame, source)

    def __calculate(self, result_frame, source: list):
        result = 0
        for item in source: 
            type, value, template = item
            matchs = len(utils.multi_match(
                result_frame, template, threshold=0.98, debug=True))
            if matchs > 0:
                print(f"{type}: {matchs}")
                result += int(value) * matchs
        print(f"result: {result}")
        return result


CubeManage = Cube()

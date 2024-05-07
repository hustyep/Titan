import time
from random import random

from src.common.constants import Charactor_Daily_Map
from src.modules.capture import capture
from src.common import utils, bot_settings, bot_action, bot_helper, bot_status
from src.common.image_template import *
from src.common.constants import *
from src.modules.chat_bot import chat_bot


class Daily:

    def __init__(self, role_name: str):
        self.role_name = role_name

        self.quest_list: list[Quest] = []
        self.cur_quest_index = 0
        self.ready = False
        self.__load_quest()

    def start(self):
        if not self.ready:
            self.__take_quest()
        return self.__start_quest()

    def pause(self):
        cur_quest = self.quest_list[self.cur_quest_index]
        cur_quest.pause()
        if cur_quest.isDone:
            self.cur_quest_index += 1

    def check(self):
        if self.cur_quest_index >= len(self.quest_list):
            return False
        cur_quest = self.quest_list[self.cur_quest_index]
        if cur_quest.isDone and self.cur_quest_index == len(self.quest_list) - 1:
            return False
        return cur_quest.isDone

    def __load_quest(self):
        map_list = Charactor_Daily_Map[self.role_name]['quest']
        if map_list is not None:
            for map in map_list:
                self.quest_list.append(Quest(map))
        else:
            raise ValueError(f"Invalid daily map list")

    def __take_quest(self):
        while has_quest():
            bot_action.mouse_move(QUEST_BUBBLE_TEMPLATE,
                                  Rect(0, 200, 100, 100),
                                  YELLOW_RANGES)
            bot_action.mouse_left_click(delay=0.3)
            bot_action.click_key(
                bot_settings.SystemKeybindings.INTERACT, delay=0.3)
            bot_action.click_key('y', delay=0.3)
            bot_action.click_key(
                bot_settings.SystemKeybindings.INTERACT, delay=0.3)
            bot_action.mouse_move_relative(10*(1 + random()), 5*(1 + random()))
        self.ready = True

    def __start_quest(self):
        while self.cur_quest_index < len(self.quest_list):
            cur_quest = self.quest_list[self.cur_quest_index]
            if cur_quest.isDone:
                self.cur_quest_index += 1
            else:
                return  cur_quest.start()
        return True


class Quest:
    def __init__(self, map_name: str, duration=160):
        self.map_name = map_name
        self.duration = duration

        self.start_time = 0
        self.last_time = 0

    @property
    def isDone(self):
        if self.last_time >= self.duration:
            return True
        if self.start_time == 0:
            return False
        return self.last_time + time.time() - self.start_time >= self.duration

    def start(self):
        if self.start_time == 0:
            self.start_time = time.time()
        return self.__prepare()

    def pause(self):
        if self.start_time == 0:
            return
        self.last_time += time.time() - self.start_time
        self.start_time = 0

    def __prepare(self):
        bot_status.enabled = False
        return self.__check_map()

    def __check_map(self):
        cur_map_name = bot_helper.identify_map_name()
        if cur_map_name != self.map_name:
            return bot_action.teleport_to_map(self.map_name)
        else:
            return True


def has_quest():
    frame = capture.frame[100:300, 0:200]
    frame = utils.filter_color(frame, YELLOW_RANGES)
    match = utils.multi_match(frame, QUEST_BUBBLE_TEMPLATE, debug=False)
    return len(match) > 0

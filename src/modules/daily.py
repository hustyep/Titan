import time

from src.common.constants import Charactor_Daily_Map


class Daily:

    def __init__(self, role_name: str):
        self.role_name = role_name

        self.quest_list: list[Quest] = []
        self.cur_quest_index = 0
        self.ready = False
        self.__load_quest()

    @property
    def current_quest(self):
        if len(self.quest_list) == 0:
            return
        if self.cur_quest_index >= len(self.quest_list):
            return
        cur_quest = self.quest_list[self.cur_quest_index]
        if cur_quest.isDone and self.cur_quest_index == len(self.quest_list) - 1:
            return
        return cur_quest

    @property
    def isDone(self):
        current_quest = self.current_quest
        if current_quest == None:
            return True
        return current_quest.isDone

    def start(self):
        if not self.ready:
            return
        if self.isDone:
            return
        current_quest = self.current_quest
        if current_quest != None:
            current_quest.start()

    def pause(self):
        if not self.ready:
            return
        if self.isDone:
            return
        current_quest = self.current_quest
        if current_quest != None:
            current_quest.pause()

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

    @property
    def is_running(self):
        if self.isDone:
            return False
        return self.start_time != 0

    def start(self):
        if self.start_time == 0:
            self.start_time = time.time()

    def pause(self):
        if self.start_time == 0:
            return
        self.last_time += time.time() - self.start_time
        self.start_time = 0

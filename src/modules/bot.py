"""An interpreter that reads and executes user-created routines."""

import threading
import time
import random
from enum import Enum
from rx.subject.subject import Subject

from src.common import utils, bot_status, bot_settings, bot_helper
from src.common.gui_setting import gui_setting
from src.common.constants import *
from src.common import bot_action
from src.common.vkeys import releaseAll
from src.modules.capture import capture
from src.modules.notifier import notifier
from src.modules.detector import detector
from src.chat_bot.chat_bot import chat_bot
from src.routine.routine import routine
from src.map.map import shared_map
from src.models.role_model import RoleModel
from src.enhance.cube import CubeManage
from src.enhance.flame import FlameManager


class BotUpdateType(Enum):
    role_loaded = 'role_loaded'


class Bot(Subject):
    """A class that interprets and executes user-defined routines."""

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__()
        self.role: RoleModel | None = None

        self.check_thread = threading.Thread(target=self._main_check)
        self.check_thread.daemon = True

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """
        Starts this Bot object's thread.
        :return:    None
        """
        notifier.subscribe(lambda e: self.on_event(e))
        utils.log_event('\n[~] Started main bot loop')
        self.thread.start()
        self.check_thread.start()

    def _main(self):
        """
        The main body of Bot that executes the user's routine.
        :return:    None
        """
        self.ready = True
        while True:
            if capture.minimap_display is None:
                utils.log_event("waiting capture...", bot_settings.debug)
                time.sleep(0.5)
            elif bot_status.enabled:
                if gui_setting.mode.type != BotRunMode.Daily and gui_setting.mode.type != BotRunMode.Farm:
                    time.sleep(1)
                elif not bot_status.prepared:
                    self.prepare()
                elif len(routine) > 0 and bot_status.player_pos != (0, 0):
                    routine.step()
                    if self.is_run_daily:
                        assert(self.role)
                        current_quest = self.role.daily.current_quest
                        if current_quest is None:
                            return
                        if current_quest.isDone:
                            bot_status.prepared = False
                        elif not current_quest.is_running:
                            current_quest.start()
                else:
                    time.sleep(0.01)
            else:
                self.identify_role()
                self.identify_map()
                time.sleep(0.3)

    def _main_check(self):
        while True:
            if self.role is not None and bot_status.enabled and capture.frame is not None:
                self.role.character.update_skill_status()
            time.sleep(0.2)

    @property
    def is_run_daily(self):
        return gui_setting.mode.type == BotRunMode.Daily and self.role is not None and self.role.daily is not None and not self.role.daily.isDone

    def prepare(self):
        if bot_status.prepared:
            return

        if not self.identify_role() and self.role is None:
            chat_bot.video_call()
            return

        if not self.check_map():
            utils.log_event("!!!check map error")
            return

        bot_status.prepared = True
        utils.log_event("prepared")

    def identify_role(self):
        role_name = bot_helper.identify_role_name()
        if not role_name:
            if self.role is None:
                utils.log_event("!!!role identify error")
            time.sleep(1)
            return False

        # update role
        if self.role == None or self.role.name != role_name:
            self.load_role(role_name)
            utils.log_event(f"~identify name:{role_name}, class:{Name_Class_Map[role_name]}")

        return True

    def identify_map(self):
        map_name = bot_helper.identify_map_name()
        if map_name is not None and map_name != shared_map.current_map_name:
            utils.log_event(f"identify map:{map_name}")
            self.load_map(map_name)

    def check_map(self):
        assert(self.role)
        
        if bot_status.lost_minimap:
            time.sleep(0.1)
            return False
        map_name = bot_helper.identify_map_name()
        utils.log_event(f"identify map:{map_name}")

        target_map = None
        match gui_setting.mode.type:
            case BotRunMode.Daily:
                target_map = self.check_daily()
            case BotRunMode.Farm:
                target_map = map_name

        if target_map == None:
            target_map = Charactor_Daily_Map[self.role.name]['default']

        # update map data
        self.load_map(target_map)

        if target_map != map_name:
            if not bot_action.teleport_to_map(target_map):
                # chat_bot.voice_call()
                chat_bot.send_message(f"teleport to {target_map} failed", capture.frame)
                return False

        assert(shared_map.current_map)
        if not bot_helper.chenck_map_available(instance=shared_map.current_map.instance):
            bot_action.change_channel(instance=shared_map.current_map.instance)
        return True

    def load_role(self, role_name):
        self.role = RoleModel(role_name)
        routine.clear()
        self.on_next(BotUpdateType.role_loaded)
        bot_settings.role = self.role

    def load_map(self, map_name: str):
        assert(self.role)

        if shared_map.current_map_name != map_name:
            shared_map.load_map(map_name)
            bot_status.reset()

        map_routine_path = f'{bot_settings.get_routines_dir(self.role.character_type.value)}\\{map_name}.csv'
        if map_routine_path != routine.path:
            routine.load(map_routine_path, self.role.character.command_book)
            bot_status.reset()

    def check_daily(self):
        if self.role is None:
            return
        if self.role.daily.isDone:
            return
        if self.role.daily.current_quest is not None:
            return self.role.daily.current_quest.map_name

    def toggle(self, enabled: bool, reason: str = ''):
        self.reset()

        if enabled:
            self.__start()
        else:
            self.__pause()

        bot_status.enabled = enabled
        utils.print_state(enabled)
        utils.log_event(reason)

    def reset(self):
        releaseAll()
        notifier.notice_time_record.clear()

        bot_status.rune_pos = None
        bot_status.rune_closest_pos = None

        bot_status.prepared = False
        capture.calibrated = False

    def __start(self):
        self.identify_role()
        if not self.role:
            return
        match gui_setting.mode.type:
            case BotRunMode.Cube:
                CubeManage.start(self.role)
            case BotRunMode.Flame:
                FlameManager.start(self.role)

    def __pause(self):
        match gui_setting.mode.type:
            case BotRunMode.Cube:
                CubeManage.stop()
            case BotRunMode.Flame:
                FlameManager.stop()
            case BotRunMode.Daily:
                if self.is_run_daily:
                    assert(self.role)
                    self.role.daily.pause()

    def on_event(self, args):
        event_type = args[0]
        if len(args) > 1:
            arg = args[1]
        else:
            arg = 0
        routine.on_bot_event(event_type)
        if isinstance(event_type, BotFatal):
            if event_type == BotFatal.BLACK_SCREEN:
                pass
            else:
                bot_status.white_room = True
                self.toggle(False, event_type.value)
                chat_bot.voice_call()
                
                bot_action.handle_white_room()
                

        elif isinstance(event_type, BotError):
            match (event_type):
                case BotError.OTHERS_STAY_OVER_120S:
                    if shared_map.current_map and not shared_map.current_map.instance:
                        bot_action.change_channel(instance=False)
                case BotError.LOST_PLAYER:
                    pass
                case (_):
                    if bot_status.enabled:
                        chat_bot.voice_call()
                    self.toggle(False, event_type.value)
        elif isinstance(event_type, BotWarnning):
            match event_type:
                # case BotWarnning.NO_MOVEMENT:
                #     bot_action.jump_down()
                case BotWarnning.OTHERS_STAY_OVER_30S:
                    if shared_map.current_map and not shared_map.current_map.instance:
                        words = ['cc pls', 'cc pls ', ' cc pls']
                        random_word = random.choice(words)
                        bot_action.say_to_all(random_word)
                case BotWarnning.OTHERS_STAY_OVER_60S:
                    if shared_map.current_map and not shared_map.current_map.instance:
                        words = ['?', 'hello?', ' cc pls', 'bro?']
                        random_word = random.choice(words)
                        bot_action.say_to_all(random_word)
                case BotWarnning.OTHERS_COMMING:
                    pass
        elif isinstance(event_type, BotInfo):
            match event_type:
                case BotInfo.RUNE_ACTIVE:
                    pass
        elif isinstance(event_type, BotVerbose):
            pass
            # match event_type:
            #     case BotVerbose.BOSS_APPEAR:
            #         threading.Timer(180, bot_action.open_boss_box).start()
        elif isinstance(event_type, BotDebug):
            if self.role:
                # bot_status.enabled = True
                self.role.character.command_book['Test_Command']().execute()
                # bot_status.enabled = False

    def bot_status(self, ext='') -> str:
        message = (
            f"bot status: {'running' if bot_status.enabled  else 'pause'}\n"
            f"rune status: {f'{time.time()}s' if bot_status.rune_pos is not None else 'clear'}\n"
            f"other players: {detector.others_count}\n"
            f"reason: {ext}\n"
        )
        return message


bot = Bot()

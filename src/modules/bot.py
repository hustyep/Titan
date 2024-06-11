"""An interpreter that reads and executes user-created routines."""

import threading
import time
from enum import Enum
from rx.subject import Subject

from src.common import utils, bot_status, bot_settings, bot_helper
from src.common.gui_setting import gui_setting
from src.common.constants import *
from src.common import bot_action
from src.common.vkeys import key_up, key_down, releaseAll
from src.modules.capture import capture
from src.modules.notifier import notifier
from src.modules.detector import detector
from src.modules.chat_bot import chat_bot
from src.command.command_book import CommandBook
from src.routine.routine import routine
from src.models.role_model import RoleModel


class BotUpdateType(Enum):
    role_loaded = 'role_loaded'


class Bot(Subject):
    """A class that interprets and executes user-defined routines."""

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__()
        self.role: RoleModel = None

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
        print('\n[~] Started main bot loop')
        self.thread.start()
        self.check_thread.start()

    def _main(self):
        """
        The main body of Bot that executes the user's routine.
        :return:    None
        """

        self.ready = True
        while True:
            if bot_status.enabled:
                if bot_status.white_room:
                    time.sleep(1)
                elif not bot_status.prepared:
                    self.prepare()
                elif len(routine) > 0 and bot_status.player_pos != (0, 0):
                    routine.step()
                    if self.daily is not None and self.daily.check():
                        bot_status.prepared = False
                else:
                    time.sleep(0.01)
            else:
                time.sleep(0.01)

    def _main_check(self):
        while True:
            if self.role.character is not None and bot_status.enabled and capture.frame is not None:
                self.role.character.update_skill_status()
            time.sleep(0.2)

    def prepare(self):
        if bot_status.prepared:
            return

        if capture.minimap_display is None:
            time.sleep(0.5)
            return

        role_name = self.identify_role()
        if not role_name:
            chat_bot.send_message("role identify error", capture.frame)
            if self.role is None:
                self.toggle(False, 'role identify error')
                return

        match gui_setting.mode.type:
            case BotRunMode.Daily:
                bot_status.enabled = False
                bot_status.enabled = self.daily.start()
                if not bot_status.enabled:
                    chat_bot.voice_call()
                    return
            case BotRunMode.Mapping, BotRunMode.Cube:
                time.sleep(1)
                return

        # update routine
        map_name = bot_helper.identify_map_name()
        print(f"identify map:{map_name}")
        if map_name is not None:
            map_routine_path = f'{bot_settings.get_routines_dir()}\\{map_name}.csv'
            if map_routine_path != routine.path:
                self.load_routine(map_routine_path)
        else:
            default_map = Charactor_Daily_Map[role_name]['default']
            bot_status.enabled = bot_action.teleport_to_map(default_map)
            return

        if not bot_helper.chenck_map_available():
            bot_action.change_channel()

        bot_status.prepared = True

    def identify_role(self):
        role_name = bot_helper.identify_role_name()
        if not role_name:
            return
        character_type = Name_Class_Map[role_name]
        if not character_type:
            return
        print(f"identify name:{role_name}, class:{character_type}")

        # update role
        if self.role == None or self.role.name != role_name:
            self.daily = None
            self.role = RoleModel(role_name)
            routine.clear()
            self.on_next(BotUpdateType.role_loaded)

        return role_name

    def load_routine(self, file: str):
        routine.load(file, self.role.character.command_book)
        bot_status.reset()

    def toggle(self, enabled: bool, reason: str = ''):
        bot_status.rune_pos = None
        bot_status.rune_closest_pos = None

        bot_status.minal_pos = None
        bot_status.minal_closest_pos = None

        bot_status.prepared = False
        capture.calibrated = False
        if enabled:
            notifier.notice_time_record.clear()
        else:
            if self.daily is not None:
                self.daily.pause()

        releaseAll()
        bot_status.enabled = enabled
        utils.print_state(enabled)
        print(reason)

    def on_event(self, args):
        event_type = args[0]
        if len(args) > 1:
            arg = args[1]
        else:
            arg = 0
        if isinstance(event_type, BotFatal):
            if event_type == BotFatal.BLACK_SCREEN:
                pass
            else:
                bot_status.white_room = True
                self.toggle(False, event_type.value)
                chat_bot.voice_call()

        elif isinstance(event_type, BotError):
            match (event_type):
                case BotError.OTHERS_STAY_OVER_120S:
                    # ActionSimulator.change_channel()
                    pass
                case BotError.LOST_PLAYER:
                    pass
                case (_):
                    self.toggle(False, event_type.value)
                    chat_bot.voice_call()
        elif isinstance(event_type, BotWarnning):
            match event_type:
                case BotWarnning.NO_MOVEMENT:
                    bot_action.jump_down()
                # case BotWarnning.OTHERS_STAY_OVER_30S:
                #     words = ['cc pls', 'cc pls ', ' cc pls']
                #     random_word = random.choice(words)
                #     ActionSimulator.say_to_all(random_word)
                # case BotWarnning.OTHERS_STAY_OVER_60S:
                #     words = ['??', 'hello?', ' cc pls', 'bro?']
                #     random_word = random.choice(words)
                #     ActionSimulator.say_to_all(random_word)
                # case BotWarnning.OTHERS_COMMING:
                    # pass
        elif isinstance(event_type, BotInfo):
            match event_type:
                case BotInfo.RUNE_ACTIVE:
                    pass
        elif isinstance(event_type, BotVerbose):
            match event_type:
                case BotVerbose.BOSS_APPEAR:
                    threading.Timer(180, bot_action.open_boss_box).start()
        elif isinstance(event_type, BotDebug):
            pass

    def bot_status(self, ext='') -> str:
        message = (
            f"bot status: {'running' if bot_status.enabled  else 'pause'}\n"
            f"rune status: {f'{time.time()}s' if bot_status.rune_pos is not None else 'clear'}\n"
            f"other players: {detector.others_count}\n"
            f"reason: {ext}\n"
        )
        return message


bot = Bot()

"""A keyboard listener to track user inputs."""

import time
import threading
import winsound
from datetime import datetime
import keyboard as kb
from src.common.interfaces import Configurable
from src.common import bot_status, utils
from src.common.gui_setting import gui_setting
from src.modules.capture import capture
from src.modules.bot import bot
from src.routine.routine import routine
from src.chat_bot.chat_bot_entity import ChatBotCommand
from src.common.action_simulator import ActionSimulator
from rx.subject import Subject
from src.map.map import map as game_map


class Listener(Configurable, Subject):
    DEFAULT_CONFIG = {
        'Start/stop': 'tab',
        'Reload routine': 'page up',
        'Record position': 'f7',
        'Add start point': 'f10',
        'Add end point': 'f11',
        'Add rope point': 'f12',
    }
    BLOCK_DELAY = 1         # Delay after blocking restricted button press

    def __init__(self):
        """Initializes this Listener object's main thread."""

        super().__init__('controls')
        self.enabled = True
        self.ready = False
        self.block_time = 0
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

        self.is_disposed = False
        self.exception = None
        self.observers = []
        self.lock = threading.RLock()
        self.is_stopped = False

    def start(self):
        """
        Starts listening to user inputs.
        :return:    None
        """

        print('\n[~] Started keyboard listener')
        self.thread.start()

    def _main(self):
        """
        Constantly listens for user inputs and updates variables in config accordingly.
        :return:    None
        """

        self.ready = True
        while True:
            if self.enabled:
                if len(self.config['Start/stop']) > 0 and kb.is_pressed(self.config['Start/stop']):
                    self.toggle_enabled()
                elif len(self.config['Reload routine']) > 0 and kb.is_pressed(self.config['Reload routine']):
                    self.reload_routine()
                elif self.restricted_pressed('Record position'):
                    self.record_position()
                elif self.restricted_pressed('Add start point'):
                    self.add_start_point()
                elif self.restricted_pressed('Add end point'):
                    self.add_end_point()
                elif self.restricted_pressed('Add rope point'):
                    self.add_rope_point()
            time.sleep(0.01)

    def restricted_pressed(self, action):
        """Returns whether the key bound to ACTION is pressed only if the bot is disabled."""

        if kb.is_pressed(self.config[action]):
            if not bot_status.enabled:
                return True
            now = time.time()
            if now - self.block_time > Listener.BLOCK_DELAY:
                print(f"\n[!] Cannot use '{action}' while Mars is enabled")
                self.block_time = now
        return False

    def toggle_enabled(self):
        """Resumes or pauses the current routine. Plays a sound to notify the user."""

        bot_status.reset()
        # notifier.notice_time_record.clear()

        bot.prepared = False
        bot.toggle(not bot_status.enabled)
        
        if bot_status.enabled:
            bot_status.started_time = time.time()
        else:
            bot_status.started_time = None

        # if bot_status.enabled:
        #     winsound.Beep(784, 333)     # G5
        # else:
        #     winsound.Beep(523, 333)     # C5
        time.sleep(0.267)

    def reload_routine(self):
        # self.recalibrate_minimap()

        # routine.load(routine.path)

        routine.clear()
        capture.calibrate = False
        bot.prepared = False
        winsound.Beep(523, 200)     # C5
        winsound.Beep(659, 200)     # E5
        winsound.Beep(784, 200)     # G5

    def record_position(self):
        pos = bot_status.player_pos
        now = datetime.now().strftime('%I:%M:%S %p')
        self.on_next(('record', pos, now))
        print(f'\n[~] Recorded position ({pos[0]}, {pos[1]}) at {now}')
        time.sleep(0.5)

    @bot_status.run_if_disabled('')
    def add_start_point(self):
        pos = bot_status.player_pos
        game_map.add_start_point((pos[0], pos[1] + 7))
        time.sleep(0.5)
        
    @bot_status.run_if_disabled('')
    def add_end_point(self):
        pos = bot_status.player_pos
        game_map.add_end_point((pos[0], pos[1] + 7))
        time.sleep(0.5)
        
    @bot_status.run_if_disabled('')
    def add_rope_point(self):
        pos = bot_status.player_pos
        game_map.add_rope_point((pos[0], pos[1] + 7))
        time.sleep(0.5)

    def on_new_command(self, command: ChatBotCommand, *args):
        match (command):
            case ChatBotCommand.INFO:
                return bot.bot_status(), None
            case ChatBotCommand.START:
                bot.toggle(True)
                return bot.bot_status(), None
            case ChatBotCommand.PAUSE:
                bot.toggle(False)
                return bot.bot_status(), None
            case ChatBotCommand.SCREENSHOT:
                filepath = utils.save_screenshot(capture.frame if capture.frame is not None else capture.camera.get_latest_frame())
                return None, filepath
            case ChatBotCommand.PRINTSCREEN:
                filepath = utils.save_screenshot(
                    capture.camera.get_latest_frame())
                return None, filepath
            case ChatBotCommand.CLICK:
                ActionSimulator.click_key(args[0])
                filepath = utils.save_screenshot(capture.frame)
                return "done", filepath
            case ChatBotCommand.LEVEL:
                level = int(args[0])
                gui_setting.notification.set('notice_level', level)
                #  TODO update UI
                return "done", None
            case ChatBotCommand.SAY:
                ActionSimulator.say_to_all(args[0])
                filepath = utils.save_screenshot(capture.frame)
                return f'said: "{args[0]}"', filepath
            case ChatBotCommand.TP:
                ActionSimulator.go_home()
                return "tp...", None
            case ChatBotCommand.CHANGE_CHANNEL:
                channel_num = 0
                if len(args) > 0:
                    channel_num = int(args[0])
                ActionSimulator.change_channel(channel_num, bot_status.enabled)
                return "changing channel...", None
            case ChatBotCommand.TEST:
                ActionSimulator.auto_login(args[0])
                filepath = utils.save_screenshot(capture.frame)
                return "login", filepath

listener = Listener()

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

class Listener(Configurable):
    DEFAULT_CONFIG = {
        'Start/stop': 'tab',
        'Reload routine': 'page up',
        'Record position': 'f12'
    }
    BLOCK_DELAY = 1         # Delay after blocking restricted button press

    def __init__(self):
        """Initializes this Listener object's main thread."""

        super().__init__('controls')
        self.enabled = False
        self.ready = False
        self.block_time = 0
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True
        self._observers = []

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
                    Listener.toggle_enabled()
                elif len(self.config['Reload routine']) > 0 and kb.is_pressed(self.config['Reload routine']):
                    self.reload_routine()
                elif self.restricted_pressed('Record position'):
                    self.record_position()
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

    @staticmethod
    def toggle_enabled():
        """Resumes or pauses the current routine. Plays a sound to notify the user."""

        # bot_status.rune_pos = None
        # notifier.notice_time_record.clear()

        if not bot_status.enabled:
            Listener.recalibrate_minimap()      # Recalibrate only when being enabled.
            bot_status.started_time = time.time()
        else:
            bot_status.started_time = None

        bot_status.enabled = not bot_status.enabled
        utils.print_state(bot_status.enabled)

        # if bot_status.enabled:
        #     winsound.Beep(784, 333)     # G5
        # else:
        #     winsound.Beep(523, 333)     # C5
        time.sleep(0.267)

    def reload_routine(self):
        self.recalibrate_minimap()

        routine.load(routine.path)

        winsound.Beep(523, 200)     # C5
        winsound.Beep(659, 200)     # E5
        winsound.Beep(784, 200)     # G5

    def recalibrate_minimap(self):
        capture.calibrated = False
        while not capture.calibrated:
            time.sleep(0.01)
        print('recalibrated')

    def record_position(self):
        pos = bot_status.player_pos
        now = datetime.now().strftime('%I:%M:%S %p')
        print(f'\n[~] Recorded position ({pos[0]}, {pos[1]}) at {now}')
        time.sleep(0.6)

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
                    filepath = utils.save_screenshot(capture.frame)
                    return None, filepath
                case ChatBotCommand.PRINTSCREEN:
                    filepath = utils.save_screenshot(capture.camera.get_latest_frame())
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
                    ActionSimulator.change_channel(channel_num)
                    return "changing channel...", None

listener = Listener()
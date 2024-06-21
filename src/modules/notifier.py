"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import os
import threading
import pygame
import keyboard as kb
from rx import operators as op
from rx.subject import Subject

from src.common import bot_status
from src.common.gui_setting import gui_setting
from src.common.image_template import *
from src.common.constants import *
from src.chat_bot.chat_bot import chat_bot
from src.modules.capture import capture
from src.modules.detector import detector
from src.routine.routine import routine

class Notifier(Subject):
    ALERTS_DIR = os.path.join('assets', 'alerts')

    _default_notice_interval = 30

    def __init__(self):
        """Initializes this Notifier object's main thread."""
        super().__init__()
        pygame.mixer.init()
        self.mixer = pygame.mixer.music
        
        self.notice_time_record = {}

    def start(self):
        """Starts this Notifier's thread."""
        capture.subscribe(lambda e: self.on_event(e))
        detector.subscribe(lambda e: self.on_event(e))
        routine.subscribe(lambda e: self.on_event(e))
        
        print('\n[~] Started notifier')

    def on_event(self, args):
        event = args[0]
        info = args[1] if len(args) > 1 else ''
        self._notify(event, info)

    def _notify(self, event: Enum, info) -> None:
        self.on_next((event, info))
        now = time.time()
        noticed_time = self.notice_time_record.get(event, 0)

        if noticed_time == 0 or now - noticed_time >= 20:
            self.notice_time_record[event] = now
            event_type = type(event)
            if event_type == BotFatal:
                threading.Thread(target=self._alert, args=('siren', )).start()
                text = f'‼️[{event.value}] {info}'
                self.send_message(text=text, image=capture.frame)
            elif event_type == BotError:
                if gui_setting.notification.get('notice_level') < 2:
                    return
                text = f'❗[{event.value}] {info}'
                self.send_message(text=text, image=capture.frame)
            elif event_type == BotWarnning:
                # if event == BotWarnning.RUNE_FAILED:
                #     info = f'{detector.rune_active_time - time.time()}s'
                
                if gui_setting.notification.get('notice_level') < 3:
                    return
                text = f'⚠️[{event.value}] {info}'
                self.send_message(text=text, image=capture.frame)
            elif event_type == BotInfo:                
                if gui_setting.notification.get('notice_level') < 4:
                    return
                text = f'💡[{event.value}] {info}'
                self.send_message(text=text)
            elif event_type == BotVerbose:
                pass
                # if event == BotVerbose.BOSS_APPEAR:
                #     threading.Timer(5, self.notify_boss_appear).start()
            elif event_type == BotDebug:
                if gui_setting.notification.get('notice_level') < 5:
                    return
                text = f'🔎[{event.value}] {info}'
                print(text)
                # self.send_message(text=text)
                
    def notify_boss_appear(self):
        bot_status.elite_boss_detected = True
        
    def send_message(self, text=None, image=None, image_path=None):
        print(text)
        chat_bot.send_message(text=text, image=image, image_path=image_path)

    def _alert(self, name, volume=0.75):
        """
        Plays an alert to notify user of a dangerous event. Stops the alert
        once the key bound to 'Start/stop' is pressed.
        """
        bot_status.enabled = False
        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play(-1)
        # TODO key
        while not kb.is_pressed('tab'):
            time.sleep(0.1)
        self.mixer.stop()
        time.sleep(2)

    def _ping(self, name, volume=0.5):
        """A quick notification for non-dangerous events."""

        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play()


def get_alert_path(name):
    return os.path.join(Notifier.ALERTS_DIR, f'{name}.mp3')

notifier = Notifier()

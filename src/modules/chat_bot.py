"""A module for sending message to telegram, wechat and email, also receiving command from telegram"""

import threading
from src.chat_bot.telegram_bot import TelegramBot
from src.chat_bot.wechat_bot import WechatBot
from src.common import bot_settings
from src.common.gui_setting import gui_setting


class ChatBot():

    def __init__(self):
        self.command_handler = None
        self.wechat_bot = WechatBot(bot_settings.wechat_name, self.on_command)
        self.telegram_bot = TelegramBot(
            bot_settings.telegram_apiToken, bot_settings.telegram_chat_id, self.on_command)

        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self, command_handler):
        self.command_handler = command_handler
        print('\n[~] Started chat bot')
        self.thread.start()

    def _main(self):
        self.wechat_bot.run()
        self.telegram_bot.run()

    def send_text(self, text):
        self.telegram_bot.send_text(text)

    def send_image(self, image=None, image_path=None):
        self.telegram_bot.send_image(image, image_path)

    def send_message(self, text=None, image=None, image_path=None):
        if gui_setting.notification.telegram:
            self.telegram_bot.send_message(text=text, image_path=image_path)
        if gui_setting.notification.wechat:
            self.wechat_bot.send_message(text=text, imagePath=image_path)

    def voice_call(self):
        self.wechat_bot.voice_call()

    def video_call(self):
        self.wechat_bot.video_call()

    def on_command(self, command, *arg):
        return self.command_handler(command, *arg)


chat_bot = ChatBot()

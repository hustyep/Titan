import time
import platform
import sys

from src.modules.bot import bot
from src.common.dll_helper import dll_helper
from src.modules.capture import capture
from src.modules.msg_capture import msg_capture
from src.modules.detector import detector
from src.modules.listener import listener
from src.modules.chat_bot import chat_bot
from src.modules.notifier import notifier
from src.modules.bot import bot
from src.modules.gui import GUI
from src.common.constants import BotFatal


def exception_hook(exc_type, exc_value, tb):
    print('Traceback:')
    filename = tb.tb_frame.f_code.co_filename
    name = tb.tb_frame.f_code.co_name
    line_no = tb.tb_lineno
    info = (
        f"File {filename} line {line_no}, in {name}\n"
        f"{exc_type.__name__}, Message: {exc_value}\n"
    )
    detector.on_next((BotFatal.CRASH, info))

    print(f"File {filename} line {line_no}, in {name}")

    # Exception type and value
    print(f"{exc_type.__name__}, Message: {exc_value}")


sys.excepthook = exception_hook

print(platform.architecture())

dll_helper.start()
while not dll_helper.ready:
    time.sleep(0.01)

capture.start()
while not capture.ready:
    time.sleep(0.01)

detector.start()
while not detector.ready:
    time.sleep(0.01)

listener.start()
while not listener.ready:
    time.sleep(0.01)

chat_bot.start(command_handler=listener.on_new_command)

notifier.start()

msg_capture.start()

bot.start()
while not bot.ready:
    time.sleep(0.01)

gui = GUI()
gui.start()

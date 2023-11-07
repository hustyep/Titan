import time
import platform 

from src.modules.bot import bot
from src.common.dll_helper import dll_helper
from src.modules.capture import capture
from src.modules.detector import detector
from src.modules.bot import bot
from src.modules.gui import GUI

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

bot.start()
while not bot.ready:
    time.sleep(0.01)
    
gui = GUI()
gui.start()


# bot.load_commands('resources/command_books/shadower.py')
# bot.command_book.Summon().execute()
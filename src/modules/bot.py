"""An interpreter that reads and executes user-created routines."""

import threading
import time
import random

from src.common import utils, bot_status
from src.modules.capture import capture
from src.map.map import map
from src.command.command_book import CommandBook
from src.routine.routine import Routine

class Bot():
    """A class that interprets and executes user-defined routines."""
    

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__()
        self.command_book: CommandBook = None
        self.routine: Routine = None

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """
        Starts this Bot object's thread.
        :return:    None
        """

        print('\n[~] Started main bot loop')
        self.thread.start()

    def _main(self):
        """
        The main body of Bot that executes the user's routine.
        :return:    None
        """

        self.ready = True
        while True:
            time.sleep(0.01)

    def load_commands(self, file):
        try:
            self.command_book = CommandBook(file)
        except Exception as e:
            print(e)
        else:
            pass
            # command_book.move.step_callback = self.point_check

    def load_routine(self, file:str):
        self.routine = Routine(file, self.command_book)

bot = Bot()

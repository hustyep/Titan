"""An interpreter that reads and executes user-created routines."""

import threading
import time
import random
from rx.subject import Subject

from src.common import utils, bot_status
from src.modules.capture import capture
from src.map.map import Map

class Bot(Subject):
    """A class that interprets and executes user-defined routines."""
    

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__()

        self.map: Map = None

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


bot = Bot()

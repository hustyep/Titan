import cv2

from model.command_book.command_book import *

class Character:

    def __init__(self, name: str, job: JobType):
        self.name = name
        self.job = job
        self.template = None
        self.command_book = None

    def load_template(self):
        try:
            role_template = cv2.imread(
                f'assets/roles/player_{self.name}_template.png', 0)
        except:
            raise ValueError(f"role template '{role_template}' is not exists.")

    def load_command_book(self):
        pass

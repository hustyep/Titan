import cv2
from character_model import *
from src.common.constants import *
from src.modules.daily import *

class RoleModel:

    def __init__(self, name: str):
        self.name = name
        self.character_type = Name_Class_Map[name]
        self.character = CharacterModel(self.character_type)
        self.name_template = self.load_role_template()
        self.daily = Daily(name)

    def load_role_template(self):
        if len(self.name) > 0:
            try:
                name_template = cv2.imread(
                    f'assets/roles/name_template_{self.name}.png', 0)
            except:
                print(f"role template '{name_template}' is not exists.")
            else:
                return name_template

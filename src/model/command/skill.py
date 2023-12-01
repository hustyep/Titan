import os
from enum import Enum
from src.common.vkeys import *
from src.common import utils
from src.modules.capture import capture
from src.common.image_template import *
from src.model.command.command import Command

class SkillType(Enum):
    Buff = 'buff'
    Switch = 'switch'
    Summon = 'summon'
    Attack = 'attack'
    Move = 'move'


class Skill(Command):
    duration:  int = 0
    type: SkillType = SkillType.Attack
    icon = None
    ready = True
    enabled = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__.load()

    @classmethod
    def load(cls):
        module_name = cls.__module__.split('.')[-1]
        path1 = f'assets/skills/{module_name}/{cls.__name__}.webp'
        path2 = f'assets/skills/{cls.__name__}.webp'
        if os.path.exists(path1):
            cls.icon = cv2.imread(path1, 0)
        elif os.path.exists(path2):
            cls.icon = cv2.imread(path2, 0)
        cls.id = cls.__name__

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return cls.ready

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        if capture.frame is None:
            return
        match cls.type:
            case SkillType.Switch:
                matchs = utils.multi_match(
                    capture.buff_frame, cls.icon[4:-4, 4:-18], threshold=0.9)
                cls.ready = len(matchs) == 0
                cls.enabled = not cls.ready
            case SkillType.Buff:
                cls.check_buff_enabled()
                if cls.enabled:
                    cls.ready = False
                else:
                    matchs = utils.multi_match(
                        capture.skill_frame, cls.icon[12:-4, 4:-4], threshold=0.99)
                    cls.ready = len(matchs) > 0
            case (_):
                matchs = utils.multi_match(
                    capture.skill_frame, cls.icon[12:-4, 4:-4], threshold=0.9)
                cls.ready = len(matchs) > 0

    @classmethod
    def check_buff_enabled(cls):
        matchs = utils.multi_match(
            capture.buff_frame, cls.icon[4:18, 18:-4], threshold=0.9)
        if not matchs:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[18:-4, 18:-4], threshold=0.9)
        cls.enabled = len(matchs) > 0
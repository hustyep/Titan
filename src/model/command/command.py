import time
from enum import Enum
from src.common.vkeys import *
from src.common import bot_status
from src.common.gui_setting import gui_setting
from src.modules.capture import capture


class Command():
    id = 'Command Superclass'
    PRIMITIVES = {int, str, bool, float}

    key: str = None
    cooldown: int = 0
    castedTime: float = 0
    precast: float = 0
    backswing: float = 0.5
    loop_begin_callback = None
    complete_callback = None

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(
                'Component superclass __init__ only accepts 1 (optional) argument: LOCALS')
        if len(kwargs) != 0:
            raise TypeError(
                'Component superclass __init__ does not accept any keyword arguments')
        if len(args) == 0:
            self.kwargs = {}
        elif type(args[0]) != dict:
            raise TypeError(
                "Component superclass __init__ only accepts arguments of type 'dict'.")
        else:
            self.kwargs = args[0].copy()
            self.kwargs.pop('__class__')
            self.kwargs.pop('self')
        self.id = self.__class__.__name__

    def __str__(self):
        variables = self.__dict__
        result = '    ' + self.id
        if len(variables) - 1 > 0:
            result += ':'
        for key, value in variables.items():
            if key != 'id=':
                result += f'\n        {key}={value}'
        # result += f'\n        kwargs={self.kwargs}'
        result += f'\n        pos={bot_status.player_pos}'
        return result

    def encode(self):
        """Encodes an object using its ID and its __init__ arguments."""
        arr = [self.id]
        for key, value in self.kwargs.items():
            if key != 'id' and type(self.kwargs[key]) in Command.PRIMITIVES:
                arr.append(f'{key}={value}')
        return ', '.join(arr)

    @bot_status.run_if_enabled
    def execute(self):
        # if gui_setting.notification.get('notice_level') >= 4:
        #     print(str(self))
        result = self.main()
        # if self.__class__.complete_callback:
        #     self.__class__.complete_callback(self)
        return result

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        if cls.cooldown == 0:
            return True

        cur_time = time.time()
        if (cur_time - cls.castedTime) > cls.cooldown + cls.backswing:
            return True

        return False

    def main(self):
        if not self.canUse():
            return False

        if len(self.__class__.key) == 0:
            return False

        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        return True


class AreaInsets:
    def __init__(self, top=0, bottom=0, left=0, right=0) -> None:
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right


class MobType(Enum):
    NORMAL = 'normal mob'
    ELITE = 'elite mob'
    BOSS = 'boss mob'


def detect_mobs(insets: AreaInsets = None,
                anchor: tuple[int, int] = None,
                type: MobType = MobType.NORMAL,
                multy_match=False,
                debug=False):
    frame = capture.frame

    if frame is None:
        return []

    match (type):
        case (MobType.BOSS):
            mob_templates = map.boss_templates
        case (MobType.ELITE):
            mob_templates = map.elite_templates
        case (_):
            mob_templates = map.mob_templates

    if len(mob_templates) == 0:
        if type == MobType.NORMAL:
            raise ValueError(f"Missing {type.value} template")
        else:
            return []

    crop = frame
    if insets is not None:
        if anchor is None:
            anchor = capture.convert_point_minimap_to_window(
                bot_status.player_pos)
        crop = frame[max(0, anchor[1]-insets.top):anchor[1]+insets.bottom,
                     max(0, anchor[0]-insets.left):anchor[0]+insets.right]

    mobs = []
    for mob_template in mob_templates:
        mobs_tmp = utils.multi_match(
            crop,
            mob_template,
            threshold=0.99 if type == MobType.NORMAL else 0.9,
            debug=debug)
        if len(mobs_tmp) > 0:
            for mob in mobs_tmp:
                mobs.append(mob)
                if not multy_match:
                    return mobs

    return mobs


def pre_detect(direction):
    anchor = capture.locate_player_fullscreen(accurate=True)
    insets = AreaInsets(top=150,
                        bottom=50,
                        left=-620 if direction == 'right' else 1000,
                        right=1000 if direction == 'right' else -620)
    matchs = []
    if gui_setting.detection.detect_elite:
        matchs = detect_mobs(insets=insets, anchor=anchor, type=MobType.ELITE)
    if not matchs and gui_setting.detection.detect_boss:
        matchs = detect_mobs(insets=insets, anchor=anchor, type=MobType.BOSS)
    return len(matchs) > 0

@bot_status.run_if_enabled
def sleep_while_move_y(interval=0.02, n=15):
    player_y = bot_status.player_pos[1]
    count = 0
    while True:
        time.sleep(interval)
        if player_y == bot_status.player_pos[1]:
            count += 1
        else:
            count = 0
            player_y = bot_status.player_pos[1]
        if count == n:
            break


@bot_status.run_if_enabled
def sleep_in_the_air(interval=0.02, n=3, start_y=0):
    if map.minimap_data is None or len(map.minimap_data) == 0:
        sleep_while_move_y(interval, n)
        return
    count = 0
    step = 0
    while True:
        y = bot_status.player_pos[1] + 7
        x = bot_status.player_pos[0]
        value = map.minimap_data[y][x]
        if value != 1 and value != 3:
            count = 0
        else:
            count += 1
        if count >= n:
            if start_y > 0:
                if start_y == bot_status.player_pos[1]:
                    break
                elif n < 8:
                    n = 8
                else:
                    break
            else:
                break
        step += 1
        if step >= 250:
            break
        time.sleep(interval)

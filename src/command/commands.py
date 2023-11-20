import time
import os
from enum import Enum
from src.common.vkeys import *
from src.common import bot_status, bot_settings, utils
from src.common.gui_setting import gui_setting
from src.map.map import map, run_if_map_available, MapPointType
from src.rune import rune
from src.modules.capture import capture
from src.common.image_template import *
from src.common.constants import *


class DefaultKeybindings:
    INTERACT = 'space'
    FEED_PET = 'L'
    Change_Channel = 'PageDn'
    Attack = 'insert'
    JUMP = 's'
    FLASH_JUMP = ';'
    ROPE_LIFT = 'b'
    ERDA_SHOWER = '`'
    MAPLE_WARRIOR = '3'
    ARACHNID = 'j'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = '='
    GUILD_POTION = "9"
    CANDIED_APPLE = '5'
    LEGION_WEALTHY = ''
    EXP_COUPON = '6'


class Keybindings(DefaultKeybindings):
    """ 'Keybindings' must be implemented in command book."""


class AreaInsets:
    def __init__(self, top=0, bottom=0, left=0, right=0) -> None:
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right


class Command():
    id = 'Command Superclass'
    PRIMITIVES = {int, str, bool, float}

    key: str = None
    cooldown: int = 0
    castedTime: float = 0
    precast: float = 0
    backswing: float = 0.5
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__.load()

    @classmethod
    def load(cls):
        module_name = cls.__module__.split('.')[-1]
        path1 = f'assets/skills/{module_name}/{cls.__name__}.png'
        path2 = f'assets/skills/{cls.__name__}.png'
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
                    capture.buff_frame, cls.icon[:, :-14], threshold=0.9)
                cls.ready = len(matchs) == 0
            case SkillType.Buff:
                matchs = utils.multi_match(
                    capture.skill_frame, cls.icon[8:, ], threshold=0.98)
                if not matchs:
                    cls.ready = False
                else:
                    matchs = utils.multi_match(
                        capture.buff_frame, cls.icon[:14, 14:], threshold=0.9)
                    if not matchs:
                        matchs = utils.multi_match(
                            capture.buff_frame, cls.icon[14:, 14:], threshold=0.9)
                    cls.ready = len(matchs) == 0
            case (_):
                matchs = utils.multi_match(
                    capture.skill_frame, cls.icon[8:, ], threshold=0.9)
                cls.ready = len(matchs) > 0


class Move(Command):

    def __init__(self, x, y, tolerance, step=1, max_steps=15):
        super().__init__(locals())
        self.target = map.platform_point((int(x), int(y)))
        self.tolerance = bot_settings.validate_nonnegative_int(tolerance)
        self.step = bot_settings.validate_nonnegative_int(step)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

    def main(self):
        if self.step > self.max_steps:
            return

        if map.minimap_data is not None and len(map.minimap_data) > 0:
            if target_reached(bot_status.player_pos, self.target, self.tolerance):
                return
        elif utils.distance(bot_status.player_pos, self.target) <= self.tolerance:
            return

        if map.on_the_rope(bot_status.player_pos):
            climb_rope(self.target[1] < bot_status.player_pos[1])

        bot_status.path = [bot_status.player_pos, self.target]
        step(self.target, self.tolerance)

        if edge_reached():
            print("-----------------------edge reached")
            pos = capture.convert_point_minimap_to_window(bot_status.player_pos)
            key_up(bot_status.player_direction)
            if bot_status.player_direction == 'left':
                mobs = detect_mobs(
                    anchor=pos, insets=AreaInsets(top=100, bottom=80, left=300, right=0))
            else:
                mobs = detect_mobs(
                    anchor=pos, insets=AreaInsets(top=100, bottom=80, left=0, right=300))
            if mobs:
                Attack().execute()

        Command.complete_callback(self)

        Move(self.target[0], self.target[1],
             self.tolerance, self.step+1, self.max_steps).execute()


#############################
#      Shared Functions     #
#############################

def step(target, tolerance):
    """
    The default 'step' function. If not overridden, immediately stops the bot.
    :param direction:   The direction in which to move.
    :param target:      The target location to step towards.
    :return:            None
    """

    print("\n[!] Function 'step' not implemented in current command book, aborting process.")
    bot_status.enabled = False


@run_if_map_available
def climb_rope(isUP=True):
    step = 0
    key = 'up' if isUP else 'down'
    while not map.on_the_platform(bot_status.player_pos):
        key_down(key)
        time.sleep(0.1)
        key_up(key)
        step += 1
        if step > 50:
            break


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


def find_next_point(start: tuple[int, int], target: tuple[int, int], tolerance: int):

    if map.minimap_data is None or len(map.minimap_data) == 0:
        return target

    if target_reached(start, target, tolerance):
        return

    d_x = target[0] - start[0]
    d_y = target[1] - start[1]
    if abs(d_x) <= tolerance:
        return target
    elif d_y < 0:
        tmp_x = (target[0], start[1])
        if target_reached(tmp_x, target, tolerance):
            return tmp_x
        if map.on_the_platform(tmp_x):
            return tmp_x
        tmp_y = (start[0], target[1])
        if map.is_continuous(tmp_y, target):
            return tmp_y
        return map.platform_point(tmp_x)
    else:
        # if abs(d_x) >= 20 and abs(d_y) >= 20:
        #     p = (start[0] + (20 if d_x > 0 else -20), target[1])
        #     if map.on_the_platform(p):
        #         return p
        tmp_x = (target[0], start[1])
        if target_reached(tmp_x, target, tolerance):
            return tmp_x
        if map.is_continuous(tmp_x, target):
            return tmp_x
        tmp_y = (start[0], target[1])
        if map.on_the_platform(tmp_y):
            return tmp_y
        return map.platform_point(tmp_y)


@run_if_map_available
def evade_rope(target: tuple[int, int] = None):
    if target is None:
        pos = bot_status.player_pos
        left = max(0, pos[0] - 1)
        right = min(pos[0] + 1, map.minimap_data.shape[1] - 1)
        has_rope = False
        for x in range(left, right + 1):
            if map.point_type((x, pos[1] + 7)) == MapPointType.FloorRope:
                has_rope = True
                break
        if has_rope:
            target_l = map.valid_point((pos[0] - 3, pos[1]))
            target_r = map.valid_point((pos[0] + 3, pos[1]))
            if map.on_the_platform(target_l):
                Walk(target_l[0], tolerance=1).execute()
            elif map.on_the_platform(target_r):
                Walk(target_r[0], tolerance=1).execute()
        return

    if map.near_rope(bot_status.player_pos):
        target_l = map.valid_point((target[0] - 3, target[1]))
        target_r = map.valid_point((target[0] + 3, target[1]))
        if map.on_the_platform(target_l):
            Walk(target_l[0], tolerance=1).execute()
        elif map.on_the_platform(target_r):
            Walk(target_r[0], tolerance=1).execute()


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


def direction_changed(direction) -> bool:
    if direction == 'left':
        return abs(bot_settings.boundary_point_r[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.boundary_point_l[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance


def edge_reached() -> bool:
    if abs(bot_settings.boundary_point_l[1] - bot_status.player_pos[1]) > 1:
        return
    if bot_status.player_direction == 'left':
        return abs(bot_settings.boundary_point_l[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.boundary_point_r[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance


def target_reached(start, target, tolerance=bot_settings.move_tolerance):
    # if tolerance > bot_settings.adjust_tolerance:
    #     return utils.distance(start, target) <= tolerance
    # else:
        return start[1] == target[1] and abs(start[0] - target[0]) <= tolerance

#############################
#      Common Command       #
#############################


class MapleWarrior(Skill):
    key = Keybindings.MAPLE_WARRIOR
    cooldown = 900
    backswing = 0.8
    type = SkillType.Buff


class ErdaShower(Skill):
    key = Keybindings.ERDA_SHOWER
    type = SkillType.Summon
    cooldown = 58
    backswing = 0.7
    duration = 60

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        if time.time() - self.castedTime > self.cooldown - 2:
            while not self.canUse():
                time.sleep(0.1)
        elif not self.canUse():
            return
        if self.direction:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        key_down('down')
        press(Keybindings.ERDA_SHOWER, 2)
        key_up('down')
        self.__class__.castedTime = time.time()
        time.sleep(self.__class__.backswing)


class Arachnid(Skill):
    key = Keybindings.ARACHNID
    type = SkillType.Attack
    cooldown = 250
    backswing = 0.9


class Walk(Command):
    """Walks in the given direction for a set amount of time."""

    def __init__(self, target_x, tolerance=5, interval=0.005, max_steps=600):
        super().__init__(locals())
        self.target_x = bot_settings.validate_nonnegative_int(target_x)
        self.interval = bot_settings.validate_nonnegative_float(interval)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)
        self.tolerance = bot_settings.validate_nonnegative_int(tolerance)

    def main(self):
        d_x = self.target_x - bot_status.player_pos[0]
        if abs(d_x) <= self.tolerance:
            return

        walk_counter = 0
        direction = 'left' if d_x < 0 else 'right'
        key_down(direction)
        while bot_status.enabled and abs(d_x) > self.tolerance and walk_counter < self.max_steps:
            new_direction = 'left' if d_x < 0 else 'right'
            if abs(d_x) <= 2:
                key_up(direction)
                press_acc(new_direction, down_time=0.02, up_time=0.03)
            else:
                if new_direction != direction:
                    key_up(direction)
                    key_down(new_direction)
                    direction = new_direction
                time.sleep(self.interval)
            walk_counter += 1
            d_x = self.target_x - bot_status.player_pos[0]
        key_up(direction)


class Wait(Command):
    """Waits for a set amount of time."""

    def __init__(self, duration):
        super().__init__(locals())
        self.duration = float(duration)

    def main(self):
        releaseAll()
        time.sleep(self.duration)


class FeedPet(Command):
    cooldown = 600
    backswing = 0.3
    key = Keybindings.FEED_PET

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        pet_settings = gui_setting.pet

        auto_feed = pet_settings.get('Auto-feed')
        if not auto_feed:
            return False

        num_pets = pet_settings.get('Num pets')
        cls.cooldown = 600 // num_pets

        return super().canUse(next_t)


class Fall(Command):
    """
    Performs a down-jump and then free-falls until the player exceeds a given distance
    from their starting position.
    """

    def main(self):
        evade_rope()
        key_down('down')
        time.sleep(0.03)
        press(Keybindings.JUMP, 1, down_time=0.1, up_time=0.1)
        key_up('down')
        sleep_in_the_air()


class SolveRune(Command):
    """
    Moves to the position of the rune and solves the arrow-key puzzle.
    :param sct:     The mss instance object with which to take screenshots.
    :return:        None
    """
    cooldown = 8
    max_attempts = 3

    def __init__(self, target, attempts=0):
        super().__init__(locals())
        self.target = target
        self.attempts = attempts

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        frame = capture.frame
        if frame is None:
            return False
        rune_buff = utils.multi_match(
            frame[:200, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
        if len(rune_buff) == 0:
            rune_buff = utils.multi_match(
                frame[:200, :], RUNE_BUFF_GRAY_TEMPLATE, threshold=0.9)
        if len(rune_buff) > 0:
            return False
        return super().canUse(next_t) and bot_status.rune_pos is not None

    def main(self):
        if not self.canUse():
            return -1, None

        bot_status.rune_solving = True
        Move(x=self.target[0], y=self.target[1], tolerance=1).execute()
        time.sleep(0.5)
        # Inherited from Configurable
        press(Keybindings.INTERACT, 1, down_time=0.2, up_time=0.8)
        # interact_result = False
        # for _ in range(3):
        #     interact_result = rune.rune_interact_result(capture.frame)
        #     if interact_result:
        #         break
        #     else:
        #         time.sleep(0.2)

        # if interact_result:
        #     pass
        # elif self.attempts < 2:
        #     return SolveRune(target=self.target, attempts=self.attempts+1).execute()
        # else:
        #     bot_status.rune_solving = False
        #     return 0, None

        print('\nSolving rune:')
        used_frame = None
        find_solution = False
        for i in range(4):
            frame = capture.frame
            solution = rune.show_magic(frame)
            if solution is None:
                return -1, frame
            if len(solution) == 4:
                print('Solution found, entering result')
                print(', '.join(solution))
                used_frame = frame
                find_solution = True
                for arrow in solution:
                    press(arrow, 1, down_time=0.1)
                self.__class__.castedTime = time.time()
                break
            time.sleep(0.1)
        time.sleep(0.2)

        bot_status.rune_solving = False
        return 1 if find_solution else -1, used_frame


class Mining(Command):
    """
    Moves to the position of the rune and solves the arrow-key puzzle.
    :param sct:     The mss instance object with which to take screenshots.
    :return:        None
    """
    max_attempts = 3

    def __init__(self, target, attempts=0):
        super().__init__(locals())
        self.target = target
        self.attempts = attempts

    def main(self):
        if bot_status.invisible:
            return

        Move(x=self.target[0], y=self.target[1], tolerance=1).execute()
        time.sleep(0.2)

        mineral_template = MINAL_HEART_TEMPLATE
        if bot_status.mineral_type == MineralType.CRYSTAL:
            mineral_template = MINAL_CRYSTAL_TEMPLATE
        elif bot_status.mineral_type == MineralType.HERB_YELLOW:
            mineral_template = HERB_YELLOW_TEMPLATE
        elif bot_status.mineral_type == MineralType.HERB_PURPLE:
            mineral_template = HERB_PURPLE_TEMPLATE

        frame = capture.frame
        matches = utils.multi_match(frame, mineral_template)
        player_template = bot_settings.role_template
        player = utils.multi_match(
            frame, player_template, threshold=0.9)
        if len(matches) > 0 and len(player) > 0:
            player_x = player[0][0]
            mineral_x = matches[0][0]
            if bot_status.mineral_type == MineralType.HERB_YELLOW or bot_status.mineral_type == MineralType.HERB_PURPLE:
                mineral_x -= 18
            if mineral_x > player_x:
                if bot_status.player_direction == 'left':
                    press('right')
                if mineral_x - player_x >= 50:
                    press('right', (mineral_x - player_x)//50)
            elif mineral_x < player_x:
                if bot_status.player_direction == 'right':
                    press('left')
                if player_x - mineral_x >= 50:
                    press('left', (player_x - mineral_x)//50)
            else:
                if bot_status.player_direction == 'right':
                    press('right')
                    press('left')
                else:
                    press('left')
                    press('right')
        else:
            if bot_status.player_direction == 'right':
                press('right', 2)
                press('left')
            else:
                press('left', 2)
                press('right')
        time.sleep(0.3)

        # Inherited from Configurable
        press(Keybindings.INTERACT, 1, down_time=0.2, up_time=0.8)

        print('\n mining:')
        frame = capture.frame
        solution = rune.show_magic(frame)
        if solution is not None:
            print(', '.join(solution))
            print('Solution found, entering result')
            for arrow in solution:
                press(arrow, 1, down_time=0.1)
        time.sleep(3.5)
        bot_status.minal_active = False
        bot_status.minal_pos = None
        bot_status.minal_closest_pos = None


class Summon(Command):
    """'Summon' command for the default command book."""

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return False


class DotAoe(Command):
    """'DotAoe' command for the default command book."""

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return False


class Attack(Command):
    """Undefined 'Attack' command for the default command book."""

    def main(self):
        print(
            "\n[!] 'Attack' command not implemented in current command book, aborting process.")
        bot_status.enabled = False


class Buff(Command):
    """Undefined 'buff' command for the default command book."""

    def main(self):
        print(
            "\n[!] 'Buff' command not implemented in current command book, aborting process.")
        bot_status.enabled = False


###################
#      Potion     #
###################

class Potion(Command):
    """Uses each of Shadowers's potion once."""

    def __init__(self):
        super().__init__(locals())
        self.potions = [
            GOLD_POTION,
            CANDIED_APPLE,
            GUILD_POTION,
            LEGION_WEALTHY,
            EXP_COUPON,
            EXP_POTION,
            WEALTH_POTION,
        ]

    def main(self):
        if bot_status.invisible:
            return False
        for potion in self.potions:
            if potion.canUse():
                potion().execute()
                time.sleep(0.3)
        return True


class EXP_POTION(Command):
    key = Keybindings.EXP_POTION
    cooldown = 7250
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class WEALTH_POTION(Command):
    key = Keybindings.WEALTH_POTION
    cooldown = 7250
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Wealthy Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GOLD_POTION(Command):
    key = Keybindings.GOLD_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Gold Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GUILD_POTION(Command):
    key = Keybindings.GUILD_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Guild Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class CANDIED_APPLE(Command):
    key = Keybindings.CANDIED_APPLE
    cooldown = 1800
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Candied Apple')
        if not enabled:
            return False
        return super().canUse(next_t)


class LEGION_WEALTHY(Command):
    key = Keybindings.LEGION_WEALTHY
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Legion Wealthy')
        if not enabled:
            return False
        return super().canUse(next_t)


class EXP_COUPON(Command):
    key = Keybindings.EXP_COUPON
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Coupon')
        if not enabled:
            return False
        return super().canUse(next_t)

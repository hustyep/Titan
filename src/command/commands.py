import time
import math
from enum import Enum
from src.common.vkeys import *
from src.common import bot_status, bot_settings, utils
from src.common.gui_setting import gui_setting
from src.map.map import map
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
    ERDA_SHOWER = '~'

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
            if key != 'id':
                result += f'\n        {key}={value}'
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
        self.main()

    def canUse(self, next_t: float = 0) -> bool:
        if self.__class__.cooldown is None:
            return True

        cur_time = time.time()
        if (cur_time + next_t - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
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

        if bot_status.player_pos[1] == self.target[1] and abs(bot_status.player_pos[0] - self.target[0] <= self.tolerance):
            return

        bot_status.path = [bot_status.player_pos, self.target]
        step(self.target, self.tolerance)
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


def sleep_in_the_air(interval=0.02, n=15):
    if not map.minimap_data:
        sleep_while_move_y(interval, n)
        return
    count = 0
    step = 0
    while True:
        value = map.minimap_data[bot_status.player_pos[0]
                                 ][bot_status.player_pos[1]+7]
        if value != 1 and value != 3:
            count += 1
        else:
            count = 0
        if count == n:
            break
        step += 1
        if step >= 250:
            break
        time.sleep(interval)


def find_next_point(start: tuple[int, int], target: tuple[int, int], tolerance: int):

    if target[1] == tolerance[1] and utils.distance(start, target) <= tolerance:
        return

    d_x = target[0] - start[0]
    if abs(d_x) <= tolerance:
        return target
    else:
        tmp_x = (target[0], start[1])
        if map.on_the_platform(tmp_x):
            return tmp_x
        tmp_y = (start[0], target[1])
        if map.on_the_platform(tmp_y):
            return tmp_y
        p = map.platform_point(tmp_x)
        return p


def evade_rope(target):
    if target is None:
        return

    if map.near_rope(bot_status.player_pos):
        target_l = (target[0] - 3, target[1])
        target_r = (target[0] + 3, target[1])
        if map.on_the_platform(target_l):
            Walk(target_l[0], tolerance=1).execute()
        elif map.on_the_platform(target_r):
            Walk(target_r[0], tolerance=1).execute()


class MobType(Enum):
    NORMAL = 'normal mob'
    ELITE = 'elite mob'
    BOSS = 'boss mob'


def detect_mobs(top=0, left=0, right=0, bottom=0, type: MobType = MobType.NORMAL, debug=False):
    frame = capture.frame
    minimap = capture.minimap

    if frame is None or minimap is None:
        return []

    match (type):
        case (MobType.BOSS):
            mob_templates = map.boss_template
        case (MobType.ELITE):
            mob_templates = map.elite_template
        case (_):
            mob_templates = map.mob_template

    if len(mob_templates) == 0:
        raise ValueError(f"Missing {type.value} template")

    if bot_settings.role_template is None:
        raise ValueError('Missing Role template')

    player_match = utils.multi_match(
        capture.frame, bot_settings.role_template, threshold=0.9)
    if len(player_match) == 0:
        # print("lost player")
        if type != MobType.NORMAL or abs(left) <= 300 and abs(right) <= 300:
            return []
        else:
            crop = frame[50:-100,]
    else:
        player_pos = (player_match[0][0] - 5, player_match[0][1] - 55)
        y_start = max(0, player_pos[1]-top)
        x_start = max(0, player_pos[0]-left)
        crop = frame[y_start:player_pos[1]+bottom,
                     x_start:player_pos[0]+right]

    mobs = []
    for mob_template in mob_templates:
        mobs_tmp = utils.multi_match(
            crop, mob_template, threshold=0.98, debug=debug)
        if len(mobs_tmp) > 0:
            for mob in mobs_tmp:
                mobs.append(mob)

    return mobs


def direction_changed() -> bool:
    if bot_status.player_direction == 'left':
        return abs(bot_settings.guard_point_r[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.guard_point_l[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance


def edge_reached() -> bool:
    if abs(bot_settings.guard_point_l[1] - bot_status.player_pos[1]) > 1:
        return
    if bot_status.player_direction == 'left':
        return abs(bot_settings.guard_point_l[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.guard_point_r[0] - bot_status.player_pos[0]) <= 1.3 * bot_settings.move_tolerance


#############################
#      Common Command       #
#############################

class ErdaShower(Command):
    key = Keybindings.ERDA_SHOWER
    cooldown = 57
    backswing = 0.7

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        while not self.canUse():
            time.sleep(0.1)
        if self.direction:
            press_acc(self.direction, down_time=0.03, up_time=0.1)
        key_down('down')
        press(Keybindings.ERDA_SHOWER)
        key_up('down')
        self.__class__.castedTime = time.time()
        time.sleep(self.__class__.backswing)


class Walk(Command):
    """Walks in the given direction for a set amount of time."""

    def __init__(self, target_x, tolerance=5, interval=0.005, max_steps=600):
        super().__init__(locals())
        self.tolerance = bot_settings.validate_nonnegative_int(tolerance)
        self.target_x = bot_settings.validate_nonnegative_int(target_x)
        self.interval = bot_settings.validate_nonnegative_float(interval)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

    def main(self):
        d_x = self.target_x - bot_status.player_pos[0]
        if abs(d_x) <= self.tolerance:
            return

        walk_counter = 0
        direction = 'left' if d_x < 0 else 'right'
        key_down(direction)
        while bot_status.enabled and abs(d_x) > self.tolerance and walk_counter < self.max_steps:
            new_direction = 'left' if d_x < 0 else 'right'
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

    def canUse(self, next_t: float = 0) -> bool:
        pet_settings = bot_settings.pets
        auto_feed = pet_settings.auto_feed.get()
        if not auto_feed:
            return False

        num_pets = pet_settings.num_pets.get()
        self.__class__.cooldown = 600 // num_pets

        return super().canUse(next_t)


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

    def canUse(self, next_t: float = 0) -> bool:
        return super().canUse(next_t) and bot_status.rune_pos is not None

    def main(self):
        if not self.canUse():
            return -1, None

        Move(x=self.target[0], y=self.target[1], tolerance=1).execute()
        time.sleep(0.5)
        # Inherited from Configurable
        press(Keybindings.INTERACT, 1, down_time=0.2, up_time=0.8)
        interact_result = False
        for _ in range(3):
            interact_result = rune.rune_interact_result(capture.frame)
            if interact_result:
                break
            else:
                time.sleep(0.2)

        if interact_result:
            self.__class__.castedTime = time.time()
        elif self.attempts < 2:
            return SolveRune(target=self.target, attempts=self.attempts+1).execute()
        else:
            return 0, None

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
                break
            time.sleep(0.1)
        time.sleep(0.2)

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

    def canUse(self, next_t: float = 0) -> bool:
        return False


class DotAoe(Command):
    """'DotAoe' command for the default command book."""

    def canUse(self, next_t: float = 0) -> bool:
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
            if potion().canUse():
                potion().execute()
                time.sleep(0.3)
        return True


class EXP_POTION(Command):
    key = Keybindings.EXP_POTION
    cooldown = 7250
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class WEALTH_POTION(Command):
    key = Keybindings.WEALTH_POTION
    cooldown = 7250
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Wealthy Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GOLD_POTION(Command):
    key = Keybindings.GOLD_POTION
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Gold Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GUILD_POTION(Command):
    key = Keybindings.GUILD_POTION
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Guild Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class CANDIED_APPLE(Command):
    key = Keybindings.CANDIED_APPLE
    cooldown = 1800
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Candied Apple')
        if not enabled:
            return False
        return super().canUse(next_t)


class LEGION_WEALTHY(Command):
    key = Keybindings.LEGION_WEALTHY
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Legion Wealthy')
        if not enabled:
            return False
        return super().canUse(next_t)


class EXP_COUPON(Command):
    key = Keybindings.EXP_COUPON
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Coupon')
        if not enabled:
            return False
        return super().canUse(next_t)

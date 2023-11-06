import time
import math
from enum import Enum
from src.common.vkeys import *
from src.common import bot_status, bot_settings, utils
from src.map.map import map
from src.rune import rune
from src.modules.capture import capture


class DefaultKeybindings:
    INTERACT = 'space'
    FEED_PET = 'L'
    Change_Channel = 'PageDn'
    Attack = 'insert'
    JUMP = 's'
    FLASH_JUMP = ';'
    ROPE_LIFT = 'b'
    ERDA_SHOWER = '~'


class Keybindings(DefaultKeybindings):
    """ 'Keybindings' must be implemented in command book."""


class Command():
    name = 'Command Superclass'
    key: str = None
    cooldown: int = 0
    castedTime: float = 0
    precast: float = 0
    backswing: float = 0.5

    def __init__(self, *args):
        super().__init__(*args)
        self.name = self.__class__.__name__

    def __str__(self):
        variables = self.__dict__
        result = '    ' + self.id
        if len(variables) - 1 > 0:
            result += ':'
        for key, value in variables.items():
            if key != 'id':
                result += f'\n        {key}={value}'
        return result

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

        super().main()
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        return True


class Move(Command):

    def __init__(self, x, y, tolerance, step=1, max_steps=15):
        super().__init__(locals())
        self.target = (int(x), int(y))
        self.tolerance = bot_settings.validate_nonnegative_int(tolerance)
        self.step = bot_settings.validate_nonnegative_int(step)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

    def main(self):
        if self.step > self.max_steps:
            return

        distance = utils.distance(bot_status.player_pos, self.target)
        if distance <= self.tolerance:
            return
        
        bot_status.path = [bot_status.player_pos, self.target]
        threshold = self.tolerance / math.sqrt(2)
        d_x = self.target[0] - bot_status.player_pos[0]
        d_y = self.target[1] - bot_status.player_pos[1]
        direction = None
        if abs(d_x) <= threshold:
            direction = 'up' if d_y < 0 else 'down'
        elif abs(d_y) <= threshold:
            direction = 'left' if d_x < 0 else 'right'
        elif utils.bernoulli(0.7):
            direction = 'left' if d_x < 0 else 'right'
        else:
            direction = 'up' if d_y < 0 else 'down'
        step(direction, self.target)

        Move(self.target[0], self.target[1],
             self.tolerance, self.step+1, self.max_steps).execute()


#############################
#      Shared Functions     #
#############################

def step(direction, target):
    """
    The default 'step' function. If not overridden, immediately stops the bot.
    :param direction:   The direction in which to move.
    :param target:      The target location to step towards.
    :return:            None
    """

    print("\n[!] Function 'step' not implemented in current command book, aborting process.")
    bot_status.enabled = False


def sleep_in_the_air():
    pass


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


class Summon(Command):
    """Undefined 'Summon' command for the default command book."""

    def canUse(self, next_t: float = 0) -> bool:
        return False


class DotAoe(Command):
    """Undefined 'DotAoe' command for the default command book."""

    def canUse(self, next_t: float = 0) -> bool:
        return False


class Buff(Command):
    """Undefined 'buff' command for the default command book."""

    def main(self):
        print(
            "\n[!] 'Buff' command not implemented in current command book, aborting process.")
        bot_status.enabled = False


###################
#      Potion     #
###################

# class Potion(Command):
#     """Uses each of Shadowers's potion once."""

#     def __init__(self):
#         super().__init__(locals())
#         self.potions = [
#             GOLD_POTION,
#             CANDIED_APPLE,
#             GUILD_POTION,
#             LEGION_WEALTHY,
#             EXP_COUPON,
#             EXP_POTION,
#             WEALTH_POTION,
#         ]

#     def main(self):
#         if bot_status.invisible:
#             return False
#         for potion in self.potions:
#             if potion().canUse():
#                 potion().execute()
#                 time.sleep(0.3)
#         return True


# class EXP_POTION(Command):
#     key = Keybindings.EXP_POTION
#     cooldown = 7250
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Exp Potion')
#         if not enabled:
#             return False
#         return super().canUse(next_t)


# class WEALTH_POTION(Command):
#     key = Keybindings.WEALTH_POTION
#     cooldown = 7250
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Wealthy Potion')
#         if not enabled:
#             return False
#         return super().canUse(next_t)


# class GOLD_POTION(Command):
#     key = Keybindings.GOLD_POTION
#     cooldown = 1810
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Gold Potion')
#         if not enabled:
#             return False
#         return super().canUse(next_t)


# class GUILD_POTION(Command):
#     key = Keybindings.GUILD_POTION
#     cooldown = 1810
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Guild Potion')
#         if not enabled:
#             return False
#         return super().canUse(next_t)


# class CANDIED_APPLE(Command):
#     key = Keybindings.CANDIED_APPLE
#     cooldown = 1800
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Candied Apple')
#         if not enabled:
#             return False
#         return super().canUse(next_t)


# class LEGION_WEALTHY(Command):
#     key = Keybindings.LEGION_WEALTHY
#     cooldown = 1810
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Legion Wealthy')
#         if not enabled:
#             return False
#         return super().canUse(next_t)


# class EXP_COUPON(Command):
#     key = Keybindings.EXP_COUPON
#     cooldown = 1810
#     backswing = 0.5

#     def canUse(self, next_t: float = 0) -> bool:
#         enabled = config.gui_settings.buffs.buff_settings.get('Exp Coupon')
#         if not enabled:
#             return False
#         return super().canUse(next_t)

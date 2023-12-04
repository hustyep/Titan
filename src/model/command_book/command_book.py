import inspect
from enum import Enum, auto
import time
from abc import ABC, abstractmethod
from src.common import bot_status, bot_settings, utils
from src.common.gui_setting import gui_setting
from src.common.image_template import *
from src.common.constants import *
from src.common.vkeys import *
from src.map.map import map, run_if_map_available, MapPointType
from src.rune import rune
from src.modules.capture import capture
from src.model.command.command import *
from src.model.command.skill import *


class ClassType(Enum):
    Explorer = auto()
    Heroes = auto()


class JobType(Enum):
    NightLord = auto()
    Shadower = auto()
    Hero = auto()
    MagicianFP = auto()


class DefaultKeybindings:
    INTERACT = 'space'
    FEED_PET = 'L'
    Change_Channel = 'o'
    Attack = 'insert'
    JUMP = 's'
    FLASH_JUMP = ';'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = ''
    GUILD_POTION = "9"
    CANDIED_APPLE = '5'
    LEGION_WEALTHY = '='
    EXP_COUPON = '6'

    # Common Skill
    FOR_THE_GUILD = '7'
    HARD_HITTER = '8'
    ROPE_LIFT = 'b'
    ERDA_SHOWER = '`'
    MAPLE_WARRIOR = '3'
    ARACHNID = 'j'
    MEMORIES = '4'
    GODDESS_BLESSING = '1'
    LAST_RESORT = '2'


class Keybindings(DefaultKeybindings):
    """ 'Keybindings' must be implemented in command book."""


class CommandBook(ABC):

    def __init__(self, job_type: JobType):
        self.job_type = job_type
        self.keybindings = Keybindings
        self.dict = {}

        self.load_commands()

    def load_commands(self):
        for name, command in inspect.getmembers(self.__module__, inspect.isclass):
            if issubclass(command, Command):
                self.dict[name.lower()] = command

    @abstractmethod
    def step(target, tolerance):
        '''implement by subclass'''

    @classmethod
    @run_if_map_available
    def evade_rope(self, target: tuple[int, int] = None):
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
                target_l = map.valid_point((pos[0] - 2, pos[1]))
                target_r = map.valid_point((pos[0] + 2, pos[1]))
                if map.on_the_platform(target_l):
                    self.Walk(target_l[0], tolerance=1).execute()
                elif map.on_the_platform(target_r):
                    self.Walk(target_r[0], tolerance=1).execute()
            return

        if map.near_rope(bot_status.player_pos):
            target_l = map.valid_point((target[0] - 2, target[1]))
            target_r = map.valid_point((target[0] + 2, target[1]))
            if map.on_the_platform(target_l):
                self.Walk(target_l[0], tolerance=1).execute()
            elif map.on_the_platform(target_r):
                self.Walk(target_r[0], tolerance=1).execute()

    @classmethod
    @run_if_map_available
    def climb_rope(self, direction):
        step = 0
        while not map.on_the_platform(bot_status.player_pos):
            key_down(direction)
            time.sleep(0.1)
            key_up(direction)
            step += 1
            if step > 50:
                break


#############################
#      Common Command       #
#############################


    class Move(Command):

        def __init__(self, x, y, tolerance, step=1, max_steps=15):
            super().__init__(locals())
            self.target = map.platform_point((int(x), int(y)))
            self.tolerance = bot_settings.validate_nonnegative_int(tolerance)
            self.step = bot_settings.validate_nonnegative_int(step)
            self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

        def step(self, target, tolerance):
            pass

        def main(self):
            if self.step > self.max_steps:
                return

            if map.minimap_data is not None and len(map.minimap_data) > 0:
                if target_reached(bot_status.player_pos, self.target, self.tolerance):
                    return
            elif utils.distance(bot_status.player_pos, self.target) <= self.tolerance:
                return

            if map.on_the_rope(bot_status.player_pos):
                CommandBook.climb_rope(
                    'up' if self.target[1] < bot_status.player_pos[1] else 'down')

            bot_status.path = [bot_status.player_pos, self.target]
            self.step(self.target, self.tolerance)

            # if edge_reached():
            #     print("-----------------------edge reached")
            #     pos = capture.convert_point_minimap_to_window(
            #         bot_status.player_pos)
            #     key_up(bot_status.player_direction)
            #     if bot_status.player_direction == 'left':
            #         mobs = detect_mobs(
            #             anchor=pos, insets=AreaInsets(top=100, bottom=80, left=300, right=0))
            #     else:
            #         mobs = detect_mobs(
            #             anchor=pos, insets=AreaInsets(top=100, bottom=80, left=0, right=300))
            #     if mobs:
            #         Attack().execute()

            # Command.complete_callback(self)

            CommandBook.Move(self.target[0], self.target[1],
                             self.tolerance, self.step+1, self.max_steps).execute()

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
                    if self.tolerance <= 1:
                        press_acc(new_direction, down_time=0.01, up_time=0.1)
                    else:
                        press_acc(new_direction, down_time=0.01, up_time=0.04)
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
            CommandBook.evade_rope()
            key_down('down')
            time.sleep(0.03)
            press(self.key, 1, down_time=0.1, up_time=0.1)
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
            return super().canUse(next_t)

        def main(self):
            if not self.canUse():
                return -1, None

            bot_status.rune_solving = True
            CommandBook.Move(
                x=self.target[0], y=self.target[1], tolerance=1).execute()
            time.sleep(0.5)
            # Inherited from Configurable
            press(self.key, 1, down_time=0.2, up_time=0.8)
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

            CommandBook.Move(
                x=self.target[0], y=self.target[1], tolerance=1).execute()
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
            press(self.key, 1, down_time=0.2, up_time=0.8)

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


#############################
#      Shared Skill       #
#############################


    class MapleWorldGoddessBlessing(Skill):
        key = Keybindings.GODDESS_BLESSING
        cooldown = 180
        precast = 0.3
        backswing = 0.85
        type = SkillType.Buff

        @classmethod
        def canUse(cls, next_t: float = 0) -> bool:
            if not CommandBook.MapleWarrior.enabled:
                return False

            return super().canUse(next_t)

    class MapleWarrior(Skill):
        key = Keybindings.MAPLE_WARRIOR
        cooldown = 900
        precast = 0.3
        backswing = 0.8
        type = SkillType.Buff

    class LastResort(Skill):
        key = Keybindings.LAST_RESORT
        cooldown = 75
        precast = 0.3
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
                self.direction = bot_settings.validate_horizontal_arrows(
                    direction)

        def main(self):
            if not self.canUse():
                return
            if self.direction:
                press_acc(self.direction, down_time=0.03, up_time=0.03)
            key_down('down')
            press(Keybindings.ERDA_SHOWER, 1)
            key_up('down')
            self.__class__.castedTime = time.time()
            time.sleep(self.__class__.backswing)

    class Arachnid(Skill):
        key = Keybindings.ARACHNID
        type = SkillType.Attack
        cooldown = 250
        backswing = 0.9

    class RopeLift(Skill):
        '''绳索'''
        key = Keybindings.ROPE_LIFT
        type = SkillType.Move
        cooldown = 3

        def __init__(self, dy: int = 20):
            super().__init__(locals())
            self.dy = abs(dy)

        def main(self):

            if self.dy >= 45:
                press(Keybindings.JUMP, up_time=0.2)
            elif self.dy >= 32:
                press(Keybindings.JUMP, up_time=0.1)
            press(self.__class__.key)
            sleep_in_the_air(n=10)

    class ForTheGuild(Skill):
        '''工会技能'''
        key = Keybindings.FOR_THE_GUILD
        cooldown = 3610
        backswing = 0.1
        type = SkillType.Buff

        @classmethod
        def canUse(cls, next_t: float = 0) -> bool:
            enabled = gui_setting.buff.get('Guild Buff')
            if not enabled:
                return False

            if CommandBook.HardHitter.enabled:
                return False

            return super().canUse(next_t)

    class HardHitter(Skill):
        '''工会技能'''
        key = Keybindings.HARD_HITTER
        cooldown = 3610
        backswing = 0.1
        type = SkillType.Buff

        @classmethod
        def canUse(cls, next_t: float = 0) -> bool:
            enabled = gui_setting.buff.get('Guild Buff')
            if not enabled:
                return False

            if CommandBook.ForTheGuild.enabled:
                return False

            return super().canUse(next_t)

        @classmethod
        def check(cls):
            cls.check_buff_enabled()
            if cls.enabled:
                cls.ready = False
            else:
                matchs = utils.multi_match(
                    capture.skill_frame, cls.icon[10:-2, 2:-2], threshold=0.98)
                cls.ready = len(matchs) > 0


#############################
#      Helper Function      #
#############################

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
        if map.is_continuous(tmp_x, target):
            return tmp_x
        tmp_y = (start[0], target[1])
        if map.on_the_platform(tmp_y):
            return tmp_y
        return map.platform_point(tmp_y)

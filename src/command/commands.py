import time
import os
from abc import ABC, abstractmethod
from enum import Enum
from src.common.vkeys import *
from src.common import bot_status, bot_settings, utils, bot_action, bot_helper
from src.common.gui_setting import gui_setting
from src.common.bot_helper import *
from src.map.map import shared_map, MapPointType
from src.rune import rune
from src.modules.capture import capture
from src.common.image_template import *
from src.common.constants import *


class DefaultKeybindings:
    INTERACT = 'space'
    FEED_PET = 'L'
    Change_Channel = 'o'
    Attack = 'insert'
    JUMP = 's'
    FLASH_JUMP = ';'
    Go_Ardentmill = '='

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "="
    GOLD_POTION = ''
    GUILD_POTION = "n"
    CANDIED_APPLE = '9'
    LEGION_WEALTHY = '7'
    EXP_COUPON = '-'

    # Common Skill
    FOR_THE_GUILD = '4'
    HARD_HITTER = '5'
    ROPE_LIFT = 'b'
    ERDA_SHOWER = '`'
    MAPLE_WARRIOR = '3'
    ARACHNID = 'w'
    GODDESS_BLESSING = '1'


class Keybindings(DefaultKeybindings):
    """ 'Keybindings' must be implemented in command book."""


class Command():
    id = 'Command Superclass'
    PRIMITIVES = {int, str, bool, float}

    key: str = None
    cooldown: int = 0
    castedTime: float = 0
    precast: float = 0.05
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

    def update(self, *args, **kwargs):
        """Updates this Component's constructor arguments with new arguments."""

        # Validate arguments before actually updating values
        self.__class__(*args, **kwargs)
        self.__init__(*args, **kwargs)

    def __str__(self):
        variables = self.__dict__
        result = '[Command]' + self.id
        # if len(variables) - 1 > 0:
        #     result += ':'
        # for key, value in variables.items():
        #     if key != 'id=':
        #         result += f'\n        {key}={value}'
        # result += f'\n        kwargs={self.kwargs}'
        # result += f'\n        pos={bot_status.player_pos}'
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
        if self.canUse():
            print(str(self))
        result = self.main()
        # if self.__class__.complete_callback:
        #     self.__class__.complete_callback(self)
        return result

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        if cls.cooldown == 0 and cls.backswing == 0:
            return True

        cur_time = time.time()
        if (cur_time + next_t - cls.castedTime) >= cls.cooldown + cls.backswing:
            return True

        return False

    def main(self, wait=True):
        if not self.canUse():
            return False

        if len(self.__class__.key) == 0:
            return False

        press_acc(self.__class__.key,
                  down_time=self.__class__.precast,
                  up_time=self.__class__.backswing if wait else 0)
        self.__class__.castedTime = time.time() - (self.__class__.backswing if wait else 0)
        return True


class Move(Command):

    def __init__(self, x, y, tolerance, step=1, max_steps=15):
        super().__init__(locals())
        self.target = shared_map.platform_point((int(x), int(y)))
        self.tolerance = bot_settings.validate_nonnegative_int(tolerance)
        self.step = bot_settings.validate_nonnegative_int(step)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

    def main(self):
        if self.step > self.max_steps:
            return

        if shared_map.minimap_data is not None and len(shared_map.minimap_data) > 0:
            if target_reached(bot_status.player_pos, self.target, self.tolerance):
                return
        elif utils.distance(bot_status.player_pos, self.target) <= self.tolerance:
            return

        if shared_map.on_the_rope(bot_status.player_pos):
            bot_action.climb_rope(self.target[1] < bot_status.player_pos[1])

        bot_status.path = [bot_status.player_pos, self.target]
        step(self.target, self.tolerance)

        Command.complete_callback(self)

        Move(self.target[0], self.target[1],
             self.tolerance, self.step+1, self.max_steps).execute()


#############################
#      Shared Functions     #
#############################

@abstractmethod
def step(target, tolerance):
    """
    The default 'step' function. If not overridden, immediately stops the bot.
    :param direction:   The direction in which to move.
    :param target:      The target location to step towards.
    :return:            None
    """

    print("\n[!] Function 'step' not implemented in current command book, aborting process.")
    bot_status.enabled = False


@bot_status.run_if_enabled
def find_next_point(start: tuple[int, int], target: tuple[int, int], tolerance: int):
    # print(f"find_next_point:\n start:{start}, target:{target}, tolerance:{tolerance}")
    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        return target

    if target_reached(start, target, tolerance):
        return

    d_x = target[0] - start[0]
    d_y = target[1] - start[1]
    if abs(d_x) <= tolerance:
        return target
    elif d_y == 0:
        if shared_map.is_continuous(start, target):
            return target
    elif d_y < 0:
        tmp_y = (start[0], target[1])
        if shared_map.is_continuous(tmp_y, target):
            return tmp_y
        tmp_x = (target[0], start[1])
        if shared_map.on_the_platform(tmp_x):
            if shared_map.is_continuous(start, tmp_x) or abs(d_x) >= 26:
                return tmp_x
    else:
        tmp_x = (target[0], start[1])
        if shared_map.is_continuous(tmp_x, start):
            return tmp_x
        tmp_y = (start[0], target[1])
        if shared_map.is_continuous(tmp_y, target):
            return tmp_y
    return shared_map.platform_point((target[0], target[1] - 1))


def find_first_gap(start: tuple[int, int], target: tuple[int, int]):
    start_x = start[0]
    end_x = target[0]
    if start_x == end_x:
        return
    if start_x < end_x:
        while True:
            if start_x < end_x and shared_map.point_type((start_x + 1, start[1])) != MapPointType.Air:
                start_x += 1
            else:
                break
        if start_x < end_x:
            return (start_x-2, start[1])
    else:
        while True:
            if start_x > 0 and shared_map.point_type((start_x - 1, start[1])) != MapPointType.Air:
                start_x -= 1
            else:
                break
        if start_x > end_x:
            return (start_x+2, start[1])


def evade_rope(up=False):
    if not shared_map.near_rope(bot_status.player_pos, up):
        return
    pos = bot_status.player_pos
    target_l = shared_map.valid_point((pos[0] - 3, pos[1]))
    target_r = shared_map.valid_point((pos[0] + 3, pos[1]))
    if shared_map.on_the_platform(target_l):
        Walk(target_l[0], tolerance=2).execute()
    elif shared_map.on_the_platform(target_r):
        Walk(target_r[0], tolerance=2).execute()


def opposite_direction(direction):
    if direction not in ['left', 'right', 'up', 'down']:
        return None
    if direction == "left":
        return 'right'
    elif direction == "right":
        return 'left'
    elif direction == "up":
        return 'down'
    else:
        return 'up'


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
#      Abstract Command     #
#############################

class Attack(ABC):
    """Undefined 'Attack' command for the default command book."""
    @abstractmethod
    def __init__(self, detect: bool):
        pass


class DoubleJump(ABC):
    """Undefined 'FlashJump' command for the default command book."""

    @abstractmethod
    def __init__(self, target: tuple[int, int], attack_if_needed=False):
        pass


class Buff(ABC):
    """Undefined 'buff' command for the default command book."""
    @abstractmethod
    def main():
        pass

#############################
#      Common Command       #
#############################


class Walk(Command):
    """Walks in the given direction for a set amount of time."""

    def __init__(self, target_x, tolerance=5, interval=0.01, max_steps=500):
        super().__init__(locals())
        self.target_x = bot_settings.validate_nonnegative_int(target_x)
        self.interval = bot_settings.validate_nonnegative_float(interval)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)
        self.tolerance = bot_settings.validate_nonnegative_int(tolerance)
        # print(str(self))

    def main(self):
        d_x = self.target_x - bot_status.player_pos[0]
        if abs(d_x) <= self.tolerance:
            return

        walk_counter = 0
        direction = 'left' if d_x < 0 else 'right'
        key_down(direction)
        while bot_status.enabled and abs(d_x) > self.tolerance and walk_counter < self.max_steps:
            # print(f"dx={d_x}")
            new_direction = 'left' if d_x < 0 else 'right'
            if self.tolerance > 0 or abs(d_x) > 1:
                if new_direction != direction:
                    key_up(direction)
                    time.sleep(0.01)
                key_down(new_direction)
                direction = new_direction
                time.sleep(self.interval)
            else:
                if direction is not None:
                    key_up(direction)
                    direction = None
                press_acc(new_direction, down_time=0.01, up_time=0.01)

            walk_counter += 1
            d_x = self.target_x - bot_status.player_pos[0]
        if direction is not None:
            key_up(direction)
        print(f"end dx={d_x}")


class Wait(Command):
    """Waits for a set amount of time."""

    def __init__(self, duration):
        super().__init__(locals())
        self.duration = float(duration)

    def main(self):
        releaseAll()
        time.sleep(self.duration)


class DetectAroundAnchor(Command):
    def __init__(self, count=1, x=0, y=0, top=315, bottom=0, left=500, right=500):
        super().__init__(locals())
        self.count = int(count)
        self.x = int(x)
        self.y = int(y)
        self.top = int(top)
        self.bottom = int(bottom)
        self.left = int(left)
        self.right = int(right)

    def main(self):
        # (469, 490)
        if self.x == 0 and self.y == 0:
            anchor = bot_helper.locate_player_fullscreen(accurate=True)
        else:
            anchor = (self.x, self.y)
        start = time.time()
        while True:
            mobs = detect_mobs_around_anchor(
                anchor=anchor,
                insets=AreaInsets(
                    top=self.top, bottom=self.bottom, left=self.left, right=self.right),
                multy_match=self.count > 1,
                debug=False)
            if len(mobs) >= self.count:
                break
            time.sleep(0.1)
            if time.time() - start > 6:
                break


class DetectInRect(Command):
    def __init__(self, count=1, x=0, y=0, width=500, height=500):
        super().__init__(locals())
        self.count = int(count)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def main(self):
        start = time.time()
        while True:
            mobs = detect_mobs_in_rect(
                rect=Rect(self.x, self.y, self.width, self.height),
                multy_match=self.count > 1,
                debug=False)
            if len(mobs) >= self.count:
                break
            time.sleep(0.1)
            if time.time() - start > 6:
                break


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


class Jump(Command):

    def __init__(self, duration, direction=None, forward=False, attack=False):
        super().__init__(locals())
        self.duration = float(duration)
        self.direction = bot_settings.validate_arrows(direction)
        self.forward = bot_settings.validate_boolean(forward)
        self.attack = bot_settings.validate_boolean(attack)

    def main(self):
        if self.direction:
            press(self.direction, down_time=0.01)
        press_acc(Keybindings.JUMP, down_time=0.01, up_time=self.duration)
        if self.forward:
            press(Keybindings.JUMP)
        if self.attack:
            Attack().execute()
        sleep_in_the_air()


class Fall(Command):
    """
    Performs a down-jump and then free-falls until the player exceeds a given distance
    from their starting position.
    """

    def __init__(self, attack=False, forward=False, buff=False):
        super().__init__(locals())
        self.attack = bot_settings.validate_boolean(attack)
        self.forward = bot_settings.validate_boolean(forward)
        self.buff = bot_settings.validate_boolean(buff)

    def main(self):
        # evade_rope()
        key_down('down')
        time.sleep(0.03)
        press(Keybindings.JUMP, 1, down_time=0.1, up_time=0.05)
        key_up('down')
        if self.attack:
            Attack().main()
        elif self.forward:
            time.sleep(0.2)
            press(Keybindings.JUMP, down_time=0.02, up_time=0.02)
            press(Keybindings.FLASH_JUMP, down_time=0.02, up_time=0.02)
        if self.buff:
            Buff().main(wait=False)

        sleep_in_the_air(n=1)


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
        rune_buff = bot_helper.rune_buff_match(frame)
        if len(rune_buff) > 0:
            return False
        return super().canUse(next_t)

    def main(self):
        if not self.canUse():
            bot_status.rune_solving = False
            bot_status.acting = False
            return -1, None
        if self.attempts >= self.max_attempts:
            bot_status.rune_solving = False
            bot_status.acting = False
            self.__class__.castedTime = time.time()
            return -1, capture.frame
        bot_status.rune_solving = True
        Move(x=self.target[0], y=self.target[1], tolerance=1).execute()
        time.sleep(0.5)
        sleep_in_the_air(n=50)
        # Inherited from Configurable
        bot_status.acting = True
        press(DefaultKeybindings.INTERACT, 1, down_time=0.3, up_time=0.5)

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
        
        if find_solution:
            # 成功激活，识别出结果，待进一步判断
            bot_status.rune_solving = False
            bot_status.acting = False
            return 1, used_frame
        elif len(bot_helper.rune_buff_match(capture.frame)) > 0:
            # 成功激活，识别失败
            self.__class__.castedTime = time.time()
            bot_status.rune_solving = False
            bot_status.acting = False
            return -1, used_frame
        else:
            # 未成功激活
            time.sleep(0.5)
            return SolveRune(self.target, self.attempts + 1).execute()


class Mining(Command):
    pass


class ChangeChannel(Command):

    def __init__(self, num: int = 0, enable=True, instance=True) -> None:
        self.num = bot_settings.validate_nonnegative_int(num)
        self.enable = bot_settings.validate_boolean(enable)
        self.instance = bot_settings.validate_boolean(instance)

    def main(self) -> None:
        bot_action.change_channel(self.num, self.enable, self.instance)


class AutoLogin(Command):

    def __init__(self, channel=33):
        super().__init__(locals())
        self.channel = bot_settings.validate_nonnegative_int(channel)

    def main(self):
        bot_action.auto_login(self.channel)


class Relogin(Command):

    def __init__(self, channel=10):
        super().__init__(locals())
        self.channel = bot_settings.validate_nonnegative_int(channel)

    def main(self):
        bot_action.relogin(self.channel)


class MapTeleport(Command):
    def main(self):
        bot_status.enabled = False
        hid.key_press('up')
        time.sleep(2)
        while (not bot_status.lost_minimap):
            time.sleep(0.1)
        while (bot_status.lost_minimap):
            time.sleep(0.1)
        time.sleep(2)
        hid.key_press('up')
        time.sleep(2)
        while (not bot_status.lost_minimap):
            time.sleep(0.1)
        while (bot_status.lost_minimap):
            time.sleep(0.1)
        time.sleep(2)
        bot_status.enabled = True


class Direction(Command):
    def __init__(self, direction):
        super().__init__(locals())
        self.direction = bot_settings.validate_arrows(direction)

    def main(self):
        if not self.direction:
            return
        # if bot_status.player_direction != self.direction:
        press(self.direction, n=1, down_time=0.02, up_time=0.01)


class Rest(Command):
    def __init__(self, wait):
        super().__init__(locals())
        self.wait = int(wait)

    def main(self):
        bot_action.teleport_random_town()
        time.sleep(self.wait)


class GoArdentmill(Command):
    def main(self):
        bot_action.go_ardentmill(Keybindings.Go_Ardentmill)

###########################
#      Abstract Skill     #
###########################


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
    update_time = 0
    tolerance = 0

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
        if cls.icon is None:
            return super().canUse(next_t)
        return cls.ready and time.time() - cls.update_time > cls.tolerance

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        if capture.frame is None:
            return
        last_state = cls.ready
        match cls.type:
            case SkillType.Switch:
                matchs = utils.multi_match(
                    capture.buff_frame, cls.icon[2:-2, 2:-16], threshold=0.9)
                cls.enabled = len(matchs) > 0
                cls.ready = not cls.enabled
            case SkillType.Buff:
                cls.check_buff_enabled()
                if cls.enabled:
                    cls.ready = False
                else:
                    matchs = utils.multi_match(
                        capture.skill_frame, cls.icon[10:-2, 4:-2], threshold=0.99)
                    cls.ready = len(matchs) > 0
            case (_):
                matchs = utils.multi_match(
                    capture.skill_frame, cls.icon[10:-2, 4:-2], threshold=0.9)
                cls.ready = len(matchs) > 0
        if not cls.ready or cls.ready != last_state:
            cls.update_time = time.time()

    @classmethod
    def check_buff_enabled(cls):
        matchs = utils.multi_match(
            capture.buff_frame, cls.icon[2:16, 16:-2], threshold=0.9)
        if not matchs:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[16:-2, 16:-2], threshold=0.9)
        cls.enabled = len(matchs) > 0


class Summon(Skill):
    """'Summon' command for the default command book."""

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return False


class DotAoe(Skill):
    """'DotAoe' command for the default command book."""

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return False


class Aoe(Skill):
    """'Aoe' command for the default command book."""

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return False


#########################
#      Common Skill     #
#########################


class MapleWorldGoddessBlessing(Skill):
    key = Keybindings.GODDESS_BLESSING
    cooldown = 180
    precast = 0.3
    backswing = 0.85
    type = SkillType.Buff

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        if not MapleWarrior.enabled:
            return False

        return super().canUse(next_t)

    @classmethod
    def load(cls):
        path = f'assets/skills/{cls.__name__}.png'
        cls.icon = cv2.imread(path, 0)
        cls.id = cls.__name__

    @classmethod
    def check(cls):
        if capture.frame is None:
            return
        cls.check_buff_enabled()
        if cls.enabled:
            cls.ready = False
        else:
            matchs = utils.multi_match(
                capture.skill_frame, cls.icon[8:,], threshold=0.99)
            cls.ready = len(matchs) > 0

    @classmethod
    def check_buff_enabled(cls):
        matchs = utils.multi_match(
            capture.buff_frame, cls.icon[:14, 14:], threshold=0.9)
        if not matchs:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[14:, 14:], threshold=0.9)
        cls.enabled = len(matchs) > 0


class ErdaShower(Skill):
    key = Keybindings.ERDA_SHOWER
    type = SkillType.Summon
    cooldown = 58
    precast = 0.4
    backswing = 0.8
    duration = 60

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    @classmethod
    def check(cls):
        if capture.frame is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[8:, : -14], threshold=0.96)
        cls.ready = len(matchs) > 0

    def main(self):
        if not self.canUse():
            return
        if self.direction:
            Direction(self.direction).execute()
        self.__class__.castedTime = time.time()
        press(Keybindings.ERDA_SHOWER, down_time=self.precast, up_time=self.backswing)


class MapleWarrior(Skill):
    key = Keybindings.MAPLE_WARRIOR
    cooldown = 900
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff


class Arachnid(Skill):
    key = Keybindings.ARACHNID
    type = SkillType.Attack
    cooldown = 250
    backswing = 0.9
    tolerance = 5

    @classmethod
    def check(cls):
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.98, debug=False)
        cls.ready = len(matchs) > 0


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

        if HardHitter.enabled:
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

        if ForTheGuild.enabled:
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


class RopeLift(Skill):
    '''绳索'''
    key = Keybindings.ROPE_LIFT
    type = SkillType.Move
    cooldown = 3
    tolerance = 1

    def __init__(self, target_y: int):
        super().__init__(locals())
        self.target_y = abs(int(target_y))

    def main(self):
        time.sleep(0.2)
        start_y = bot_status.player_pos[1]
        dy = abs(start_y - self.target_y)
        while not self.canUse:
            time.sleep(1)
        print(f"target_y: {self.target_y} start_y: {start_y}")
        if dy >= 50:
            press_acc(Keybindings.JUMP, up_time=0.2)

        press(self.key)
        # 50：0.97
        # 42：
        if dy >= 55:
            pass  
        elif dy >= 50:
            time.sleep(0.97)
            press(self.key)
        elif dy >= 40:
            time.sleep(0.2075)
            press(self.key)
        else:
            time.sleep(0.24)
            press(self.key)            
        sleep_in_the_air(n=30)

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
            EXP_Potion,
            Wealth_Potion,
        ]

    def main(self):
        if bot_status.invisible:
            return False
        for potion in self.potions:
            if potion.canUse():
                potion().execute()
                time.sleep(0.2)
        return True


class EXP_Potion(Command):
    key = Keybindings.EXP_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class Wealth_Potion(Command):
    key = Keybindings.WEALTH_POTION
    cooldown = 1810
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
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Candied Apple')
        if not enabled:
            return False
        return super().canUse(next_t)


class LEGION_WEALTHY(Command):
    key = Keybindings.LEGION_WEALTHY
    cooldown = 610
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Legion Wealthy')
        if not enabled:
            return False
        return super().canUse(next_t)


class EXP_COUPON(Command):
    key = Keybindings.EXP_COUPON
    cooldown = 310
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Coupon')
        if not enabled:
            return False
        return super().canUse(next_t)

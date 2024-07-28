import time
import os
from abc import ABC, abstractmethod
from enum import Enum
from random import randrange
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
    FEED_PET = 'l'
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
    LAST_RESORT = '4'
    FOR_THE_GUILD = '4'
    HARD_HITTER = '5'
    ROPE_LIFT = 'b'
    ERDA_SHOWER = '`'
    MAPLE_WARRIOR = '3'
    ARACHNID = 'w'
    GODDESS_BLESSING = '1'
    SolarCrest = '5'
    Will_of_Erda = 'home'
    Sol_Janus_Dawn = 't'
    Sol_Janus = ';'


class Command():
    id = 'Command Superclass'
    PRIMITIVES = {int, str, bool, float}

    key: str | None = None
    cooldown: float = 0
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
        result = f'[Command]{self.id}: pos={bot_status.player_pos.tuple}, dir={bot_status.player_direction}, moving={bot_status.player_moving}'
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
        if self.__class__.canUse():
            utils.log_event(str(self), bot_settings.debug)
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

        if not self.__class__.key:
            return False

        press_acc(self.__class__.key,
                  down_time=self.__class__.precast,
                  up_time=self.__class__.backswing if wait else 0)
        self.__class__.castedTime = time.time() - (self.__class__.backswing if wait else 0)
        return True


class Move(Command):

    def __init__(self, x, y, tolerance, step=1, max_steps=15):
        super().__init__(locals())
        self.target = shared_map.platform_point(
            MapPoint(int(x), int(y), bot_settings.validate_nonnegative_int(tolerance)))
        self.step = bot_settings.validate_nonnegative_int(step)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

    def __str__(self):
        result = super().__str__()
        result += f' target={self.target.tuple} tolerance={self.target.tolerance} step={self.step}'
        return result

    def main(self, wait=True):
        if self.step > self.max_steps:
            print(f"[Failed][Move] pos={bot_status.player_pos.tuple} target={str(self.target)}", True)
            DoubleJump(self.target).execute()
            return False

        if shared_map.data_available and target_reached(bot_status.player_pos, self.target):
            return True

        if shared_map.point_type(bot_status.player_pos) == MapPointType.FloorRope:
            press("up", down_time=0.1)

        if shared_map.on_the_rope(bot_status.player_pos):
            bot_action.climb_rope(self.target.y < bot_status.player_pos.y)

        bot_status.path = [bot_status.player_pos, self.target]
        step(self.target)

        if Command.complete_callback:
            Command.complete_callback(self)

        return Move(self.target.x, self.target.y, self.target.tolerance, self.step+1, self.max_steps).execute()


#############################
#      Shared Functions     #
#############################

@abstractmethod
def step(target: MapPoint):
    """
    The default 'step' function. If not overridden, immediately stops the bot.
    :param direction:   The direction in which to move.
    :param target:      The target location to step towards.
    :return:            None
    """

    print("\n[!] Function 'step' not implemented in current command book, aborting process.")
    bot_status.enabled = False


@bot_status.run_if_enabled
def find_next_point(start: MapPoint, target: MapPoint):
    # print(f"find_next_point:\n start:{start}, target:{target}, tolerance:{tolerance}")
    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        return target

    if target_reached(start, target):
        return

    d_x = target.x - start.x
    d_y = target.y - start.y
    if abs(d_x) <= target.tolerance:
        return target
    elif d_y == 0:
        if shared_map.is_continuous(start, target):
            return target
    elif d_y < 0:
        tmp_y = MapPoint(start.x, target.y, target.tolerance)
        if shared_map.is_continuous(tmp_y, target):
            return tmp_y
        tmp_x = MapPoint(target.x, start.y, target.tolerance)
        if shared_map.on_the_platform(tmp_x):
            if shared_map.is_continuous(start, tmp_x) or abs(d_x) >= 26:
                return tmp_x
    else:
        tmp_x = MapPoint(target.x, start.y, target.tolerance)
        if shared_map.is_continuous(tmp_x, start):
            return tmp_x
        tmp_y = MapPoint(start.x, target.y, target.tolerance)
        if shared_map.is_continuous(tmp_y, target):
            return tmp_y
    return shared_map.platform_point(MapPoint(target.x, target.y - 1, target.tolerance))


def find_first_gap(start: tuple[int, int], target: tuple[int, int]):
    start_x = start[0]
    end_x = target[0]
    if start_x == end_x:
        return
    if start_x < end_x:
        while True:
            if start_x < end_x and shared_map.point_type(MapPoint(start_x + 1, start[1])) != MapPointType.Air:
                start_x += 1
            else:
                break
        if start_x < end_x:
            return (start_x-2, start[1])
    else:
        while True:
            if start_x > 0 and shared_map.point_type(MapPoint(start_x - 1, start[1])) != MapPointType.Air:
                start_x -= 1
            else:
                break
        if start_x > end_x:
            return (start_x+2, start[1])


@bot_status.run_if_enabled
def evade_rope(up=False):
    if not shared_map.near_rope(bot_status.player_pos, up):
        return
    pos = bot_status.player_pos
    pos = shared_map.fixed_point(pos)
    plat = shared_map.platform_of_point(pos)
    if not plat:
        return
    direction = 'left' if pos.x - plat.begin_x > plat.end_x - pos.x else 'right'
    press(direction, down_time=0.1)
    

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
        return abs(bot_settings.boundary_point_r[0] - bot_status.player_pos.x) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.boundary_point_l[0] - bot_status.player_pos.x) <= 1.3 * bot_settings.move_tolerance


def edge_reached() -> bool:
    if abs(bot_settings.boundary_point_l[1] - bot_status.player_pos.y) > 1:
        return False
    if bot_status.player_direction == 'left':
        return abs(bot_settings.boundary_point_l[0] - bot_status.player_pos.x) <= 1.3 * bot_settings.move_tolerance
    else:
        return abs(bot_settings.boundary_point_r[0] - bot_status.player_pos.x) <= 1.3 * bot_settings.move_tolerance


def target_reached(start: MapPoint, target: MapPoint):
    # if tolerance > bot_settings.adjust_tolerance:
    #     return utils.distance(start, target) <= tolerance
    # else:
    return abs(start.y - target.y) <= target.tolerance_v and abs(start.x - target.x) <= target.tolerance


def random_direction():
    if random() > 0.5:
        return 'left'
    else:
        return 'right'

#############################
#      Abstract Command     #
#############################


class Attack(Command):
    """Undefined 'Attack' command for the default command book."""
    @abstractmethod
    def __init__(self):
        pass


class DoubleJump(Command):
    """Undefined 'FlashJump' command for the default command book."""

    def __init__(self, target: MapPoint, attack_if_needed=False):
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

    def __init__(self, target: MapPoint, use_portal=False, max_steps=15):
        super().__init__(locals())
        self.target = target
        self.use_portal = bot_settings.validate_boolean(use_portal)
        self.max_steps = bot_settings.validate_nonnegative_int(max_steps)

    def main(self, wait=True):
        d_x = self.target.x - bot_status.player_pos.x
        if abs(d_x) <= self.target.tolerance:
            return True

        walk_counter = 0
        if self.use_portal:
            key_down('up')
        while bot_status.enabled and abs(d_x) > self.target.tolerance and walk_counter < self.max_steps:
            if abs(bot_status.player_pos.y - self.target.y) > self.target.tolerance_v:
                break
            d_x = self.target.x - bot_status.player_pos.x
            direction = 'left' if d_x < 0 else 'right'
            sleep_time = 0
            # if bot_status.player_direction != direction:
            #     # 转身时间
            #     sleep_time += 0.08
            # if not bot_status.player_moving:
            #     # 启动时间
            #     sleep_time += 0.08
            if abs(d_x) > 1:
                sleep_time = (abs(d_x) - 1) * 0.07
            else:
                sleep_time = 0.05
            key_down(direction)
            time.sleep(sleep_time)
            key_up(direction)
            walk_counter += 1
            time.sleep(0.2)
            d_x = self.target.x - bot_status.player_pos.x
            print(f"[walk] step={walk_counter} pos={bot_status.player_pos.tuple}")
        print(f"end dx={d_x}")
        if self.use_portal:
            key_up('up')
        return abs(d_x) <= self.target.tolerance


class Wait(Command):
    """Waits for a set amount of time."""

    def __init__(self, duration):
        super().__init__(locals())
        self.duration = float(duration)

    def main(self, wait=True):
        releaseAll()
        time.sleep(self.duration)
        return True


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

    def main(self, wait=True):
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
        return True


class DetectInRect(Command):
    def __init__(self, count=1, x=0, y=0, width=500, height=500):
        super().__init__(locals())
        self.count = int(count)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def main(self, wait=True):
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
        return True


class FeedPet(Command):
    cooldown = 600
    backswing = 0.3
    key = DefaultKeybindings.FEED_PET

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        pet_settings = gui_setting.pet

        auto_feed = pet_settings.get('Auto-feed')
        if not auto_feed:
            return False

        num_pets = int(pet_settings.get('Num pets'))
        cls.cooldown = 600 // num_pets

        return super().canUse(next_t)


class Jump(Command):

    def __init__(self, duration, direction=None, forward=False, attack=False):
        super().__init__(locals())
        self.duration = float(duration)
        self.direction = bot_settings.validate_arrows(direction)
        self.forward = bot_settings.validate_boolean(forward)
        self.attack = bot_settings.validate_boolean(attack)

    def main(self, wait=True):
        if self.direction:
            press(self.direction, down_time=0.01)
        press_acc(DefaultKeybindings.JUMP,
                  down_time=0.01, up_time=self.duration)
        if self.forward:
            press(DefaultKeybindings.JUMP)
        if self.attack:
            Attack().execute()  # type: ignore
        sleep_in_the_air()
        return True


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

    def main(self, wait=True):
        evade_rope()
        key_down('down')
        time.sleep(0.03)
        sleep_in_the_air(n=4)
        press(DefaultKeybindings.JUMP, 1, down_time=0.1, up_time=0.05)
        if self.attack:
            key_up('down')
            Attack().main()
        elif self.forward:
            key_up('down')
            time.sleep(0.2)
            press(DefaultKeybindings.JUMP, down_time=0.02, up_time=0.02)
            press(DefaultKeybindings.FLASH_JUMP, down_time=0.02, up_time=0.02)
        if self.buff:
            key_up('down')
            Buff().main(wait=False)  # type: ignore
        time.sleep(0.4)
        sleep_in_the_air(n=2, detect_rope=True)
        key_up('down')
        return True


class Use_Portal(Command):

    def __init__(self, portal: Portal, count=0):
        self.portal = portal
        self.count = count

    def main(self, wait=True):
        if target_reached(bot_status.player_pos, self.portal.entrance):
            press('up', down_time=0.3)
            return True
        else:
            Move(self.portal.entrance.x, self.portal.entrance.y, 5).execute()
            Walk(self.portal.entrance, use_portal=True).execute()
            return True


class Jump_Around(Command):

    def __init__(self, direction=None):
        self.direction = bot_settings.validate_horizontal_arrows(direction)
        if self.direction is None:
            self.direction = random_direction()

    def main(self, wait=True):
        direction = self.direction
        key_down(direction)
        time.sleep(0.01)
        press(DefaultKeybindings.JUMP, 2, 0.02, 0.02)
        key_up(direction)
        time.sleep(0.01)
        Attack().execute()
        sleep_in_the_air()
        key_down(opposite_direction(direction))
        time.sleep(0.01)
        press(DefaultKeybindings.JUMP, 2, 0.02, 0.02)
        key_up(opposite_direction(direction))
        time.sleep(0.01)
        Attack().execute()
        sleep_in_the_air()
        return True


class Walk_Around(Command):
    def main(self, wait=True):
        plat = shared_map.platform_of_point(bot_status.player_pos)
        if not plat:
            return False
        direction = 'left' if plat.begin_x - bot_status.player_pos.x >= plat.end_x - bot_status.player_pos.x else 'right'
        walk_time = 1 * random()
        press(direction, down_time=walk_time)
        Attack().execute()
        press(opposite_direction(direction), down_time=walk_time)
        return True


class Random_Action(Command):
    def main(self, wait=True):
        match randrange(0, 4):
            case 0:
                Jump_Around().execute()
            case 1:
                Jump(0.2, attack=True).execute()
            case 2:
                Jump(0.1, attack=True).execute()
                Jump(0.1, attack=True).execute()
            case 3:
                Walk_Around().execute()
        return True


class Collect_Boss_Essence(Command):
    def main(self, wait=True):
        Walk_Around().execute()
        time.sleep(0.1)
        Fall().execute()
        time.sleep(0.1)
        Jump_Around().execute()
        return True


class SolveRune(Command):
    """
    Moves to the position of the rune and solves the arrow-key puzzle.
    :param sct:     The mss instance object with which to take screenshots.
    :return:        None
    """
    cooldown = 7
    max_attempts = 3

    def __init__(self, target: MapPoint, attempts=0):
        super().__init__(locals())
        self.target = target
        self.attempts = attempts

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        frame = capture.frame
        if frame is None:
            return False
        # rune_buff = bot_helper.rune_buff_match(frame)
        # if len(rune_buff) > 0:
        #     return False
        return super().canUse(next_t)

    def main(self, wait=True):  # type: ignore
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
        Move(x=self.target.x, y=self.target.y, tolerance=1).execute()
        time.sleep(0.3)
        sleep_in_the_air(n=10)
        # Inherited from Configurable
        bot_status.acting = True
        press(DefaultKeybindings.INTERACT, 1, down_time=0.3, up_time=0.3)

        print('\nSolving rune:')
        used_frame = None
        find_solution = False
        frame = capture.frame
        solution = rune.show_magic(frame)
        if solution is not None and len(solution) == 4:
            print('Solution found, entering result')
            print(', '.join(solution))
            used_frame = frame
            for arrow in solution:
                press(arrow, 1, down_time=0.1)
        bot_status.acting = False
        time.sleep(0.3)
        buff_count = len(bot_helper.rune_buff_match(capture.frame))
        if buff_count == 1:
            print("成功激活，识别失败")
            self.__class__.castedTime = time.time()
            bot_status.rune_solving = False
            return -1, used_frame
        elif buff_count > 1:
            print("成功激活，识别出结果，待进一步判断")
            self.__class__.castedTime = time.time()
            bot_status.rune_solving = False
            return 1, used_frame
        else:
            print("未成功激活")
            time.sleep(0.5)
            return SolveRune(self.target, self.attempts + 1).execute()


class Mining(Command):
    pass


class ChangeChannel(Command):

    def __init__(self, num: int = 0, enable=True, instance=True) -> None:
        self.num = bot_settings.validate_nonnegative_int(num)
        self.enable = bot_settings.validate_boolean(enable)
        self.instance = bot_settings.validate_boolean(instance)

    def main(self, wait=True):
        bot_action.change_channel(self.num, self.instance)
        return True


class AutoLogin(Command):

    def __init__(self, channel=33):
        super().__init__(locals())
        self.channel = bot_settings.validate_nonnegative_int(channel)

    def main(self, wait=True):
        bot_action.auto_login(self.channel)
        return True


class Relogin(Command):

    def __init__(self, channel=10):
        super().__init__(locals())
        self.channel = bot_settings.validate_nonnegative_int(channel)

    def main(self, wait=True):
        bot_action.relogin(self.channel)
        return True


class MapTeleport(Command):
    def main(self, wait=True):
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
        return True


class Direction(Command):
    def __init__(self, direction):
        super().__init__(locals())
        self.direction = bot_settings.validate_arrows(direction)

    def __str__(self):
        result = f'[Command]{self.id}: {self.direction} pos={bot_status.player_pos.tuple}'
        return result

    def main(self, wait=True):
        if not self.direction:
            print(f'[Command]{self.id}: {self.direction} not executed')
            return False
        if bot_status.player_direction != self.direction:
            press(self.direction, n=1, down_time=0.03, up_time=0.01)
            return True
        return False


class Rest(Command):
    def __init__(self, wait):
        super().__init__(locals())
        self.wait = int(wait)

    def main(self, wait=True):
        if bot_action.teleport_random_town():
            time.sleep(self.wait)
            return True
        return False


# class GoArdentmill(Command):
#     def main(self):
#         bot_action.go_ardentmill(DefaultKeybindings.Go_Ardentmill)

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

    def __str__(self):
        result = f'[Skill]{self.id}: pos={bot_status.player_pos.tuple}'
        return result

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
                        capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.99)
                    cls.ready = len(matchs) > 0
            case (_):
                matchs = utils.multi_match(
                    capture.skill_frame, cls.icon[2:-2, 14:-1], threshold=0.99)
                cls.ready = len(matchs) > 0
        if not cls.ready or cls.ready != last_state:
            cls.update_time = time.time()

    @classmethod
    def check_buff_enabled(cls):
        if cls.icon is None:
            return
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


class Pre_Burst(Command):
    def main(self, wait=True):
        pass


class Burst(Command):
    def main(self, wait=True):
        pass

#########################
#      Common Skill     #
#########################


class LastResort(Skill):
    key = DefaultKeybindings.LAST_RESORT
    cooldown = 75
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff


class MapleWorldGoddessBlessing(Skill):
    key = DefaultKeybindings.GODDESS_BLESSING
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
    key = DefaultKeybindings.ERDA_SHOWER
    type = SkillType.Summon
    cooldown = 58
    precast = 0.3
    backswing = 0.6
    duration = 60

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        if capture.frame is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[8:, : -14], threshold=0.96)
        cls.ready = len(matchs) > 0

    def main(self, wait=True):
        if not self.canUse():
            return False
        if self.direction:
            Direction(self.direction).execute()
        self.__class__.castedTime = time.time()
        press(DefaultKeybindings.ERDA_SHOWER,
              down_time=self.precast, up_time=self.backswing)
        return True


class Sol_Janus(Command):
    key = DefaultKeybindings.Sol_Janus
    type = SkillType.Summon
    cooldown = 3
    precast = 0.2
    backswing = 0.2

    # 1: dusk; 2: dawn
    def __init__(self, type: int):
        super().__init__(locals())
        self.type = bot_settings.validate_nonnegative_int(type)

    def main(self, wait=True):
        press(self.key, down_time=0.5, up_time=0.2)
        press('right' if self.type == 1 else 'left', down_time=0.03)
        return True


class Sol_Janus_Dawn(Command):
    key = DefaultKeybindings.Sol_Janus_Dawn
    type = SkillType.Summon
    cooldown = 60
    precast = 0.3
    backswing = 0.6
    duration = 120
    count = 3

    def __init__(self, direction=None, jump=False):
        super().__init__(locals())
        self.jump = bot_settings.validate_boolean(jump)
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if self.direction:
            Direction(self.direction).execute()
        if self.jump:
            press(DefaultKeybindings.JUMP)
        press(self.key, down_time=0.6)
        return True


class Will_of_Erda(Command):
    key = DefaultKeybindings.Will_of_Erda
    cooldown = 330
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff


class MapleWarrior(Skill):
    key = DefaultKeybindings.MAPLE_WARRIOR
    cooldown = 900
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff


class Arachnid(Skill):
    key = DefaultKeybindings.ARACHNID
    type = SkillType.Attack
    cooldown = 250
    backswing = 0.9
    tolerance = 5

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.98, debug=False)
        cls.ready = len(matchs) > 0


class SolarCrest(Skill):
    key = DefaultKeybindings.SolarCrest
    type = SkillType.Attack
    cooldown = 240
    precast = 0.1
    backswing = 0.75
    tolerance = 5


class ForTheGuild(Skill):
    '''工会技能'''
    key = DefaultKeybindings.FOR_THE_GUILD
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
    key = DefaultKeybindings.HARD_HITTER
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

    # @classmethod
    # def check(cls):
    #     cls.check_buff_enabled()
    #     if cls.enabled:
    #         cls.ready = False
    #     elif cls.icon:
    #         matchs = utils.multi_match(
    #             capture.skill_frame, cls.icon[10:-2, 2:-2], threshold=0.98)
    #         cls.ready = len(matchs) > 0


class RopeLift(Skill):
    '''绳索'''
    key = DefaultKeybindings.ROPE_LIFT
    type = SkillType.Move
    cooldown = 3
    tolerance = 1

    def __init__(self, target_y: int):
        super().__init__(locals())
        self.target_y = abs(int(target_y))

    def main(self, wait=True):
        time.sleep(0.2)
        start_y = bot_status.player_pos.y
        dy = abs(start_y - self.target_y)
        while not self.canUse:
            time.sleep(1)
        print(f"target_y: {self.target_y} start_y: {start_y}")
        if dy >= 50:
            press_acc(DefaultKeybindings.JUMP, up_time=0.2)

        press_acc(self.key)
        # 50：0.97
        # 42：
        has_upper_plat = False
        for y in range(0, self.target_y):
            if shared_map.is_floor_point(MapPoint(bot_status.player_pos.x, y)):
                has_upper_plat = True
                break
        if dy >= 55 or not has_upper_plat:
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
        # sleep_in_the_air(n=30)
        return True

###################
#      Potion     #
###################


class EXP_Potion(Command):
    key = DefaultKeybindings.EXP_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class Wealth_Potion(Command):
    key = DefaultKeybindings.WEALTH_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Wealthy Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GOLD_POTION(Command):
    key = DefaultKeybindings.GOLD_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Gold Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GUILD_POTION(Command):
    key = DefaultKeybindings.GUILD_POTION
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Guild Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class CANDIED_APPLE(Command):
    key = DefaultKeybindings.CANDIED_APPLE
    cooldown = 1810
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Candied Apple')
        if not enabled:
            return False
        return super().canUse(next_t)


class LEGION_WEALTHY(Command):
    key = DefaultKeybindings.LEGION_WEALTHY
    cooldown = 610
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Legion Wealthy')
        if not enabled:
            return False
        return super().canUse(next_t)


class EXP_COUPON(Command):
    key = DefaultKeybindings.EXP_COUPON
    cooldown = 310
    backswing = 0.5

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        enabled = gui_setting.buff.get('Exp Coupon')
        if not enabled:
            return False
        return super().canUse(next_t)

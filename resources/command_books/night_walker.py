"""A collection of all commands that Night Walker can use to interact with the game. 	"""

import time
import cv2

from src.common import bot_status, bot_settings, utils
from src.common.gui_setting import gui_setting
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc
from src.routine.components import *
from src.command.commands import *
# from src.command.commands import Command, Skill, Walk, Fall, Direction, RopeLift, Arachnid, LastResort, ForTheGuild, HardHitter, SkillType, sleep_in_the_air, target_reached, evade_rope, opposite_direction, detect_mobs_around_anchor
from src.map.map_helper import *
from src.map.map import shared_map
from src.modules.capture import capture
from src.chat_bot.chat_bot import chat_bot

# List of key mappings


class Keybindings:
    # Movement
    JUMP = 's'
    Shadow_Jump = 'g'
    Shadow_Dodge = 'a'
    ROPE_LIFT = 'b'

    # Buffs
    Transcendent_Cygnus_Blessing = '1'
    Glory_of_the_Guardians = '2'
    Shadow_Illusion = '3'
    LAST_RESORT = '4'
    Shadow_Spear = 'v'
    Shadow_Bat = 'f1'
    Dark_Elemental = 'f3'
    Darkness_Ascending = '6'
    FOR_THE_GUILD = '8'
    HARD_HITTER = '7'
    Cygnus_Knights_Will = 'end'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "="
    GOLD_POTION = ""
    GUILD_POTION = "n"
    CANDIED_APPLE = '9'
    LEGION_WEALTHY = ''
    EXP_COUPON = '-'

    # Skills
    Quintuple_Star = 'f'
    Dark_Omen = 'r'
    Dominion = 'c'
    ERDA_SHOWER = '`'
    Phalanx_Charge = 'z'
    Greater_Dark_Servant = 'd'
    Shadow_Bite = 'e'
    Rapid_Throw = 'x'
    Silence = 'j'
    ARACHNID = 'w'
    SolarCrest = '5'


#########################
#       Movement        #
#########################


@bot_status.run_if_enabled
def step(target: MapPoint):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    # utils.log_event(f"[step]target:{str(target)}", bot_settings.debug)s
    next_p = find_next_point(bot_status.player_pos, target)
    utils.log_event(f"[step]next_p:{str(next_p)}", bot_settings.debug)
    if not next_p:
        return

    bot_status.path = [bot_status.player_pos, next_p, target]

    d_y = next_p.y - bot_status.player_pos.y
    if abs(d_y) > target.tolerance_v:
        if d_y > 0:
            move_down(next_p)
        else:
            move_up(next_p)
    else:
        move_horizontal(next_p)


@bot_status.run_if_enabled
def move_horizontal(target: MapPoint):
    start_p = shared_map.fixed_point(bot_status.player_pos)
    d_x = target.x - start_p.x
    distance = abs(d_x)

    if not shared_map.is_continuous(start_p, target):
        DoubleJump(target=target, attack_if_needed=True).execute()
    elif distance >= DoubleJump.move_range.start:
        DoubleJump(target=target, attack_if_needed=True).execute()
    elif distance >= 15 or distance in range(7, 10):
        DoubleJump(target=target, attack_if_needed=False).execute()
    elif distance >= Shadow_Dodge.move_range.start:
        Shadow_Dodge('left' if d_x < 0 else 'right').execute()
    else:
        Walk(target).execute()


@bot_status.run_if_enabled
def move_up(target: MapPoint):
    p = bot_status.player_pos
    dy = abs(p.y - target.y)

    up_point = MapPoint(p.x, target.y)
    if not shared_map.is_continuous(up_point, target):
        # 跨平台
        DoubleJump(target, False)
        return

    
    next_platform = shared_map.platform_of_point(target)
    assert (next_platform)
    if up_point.x - next_platform.begin_x <= 10 and bot_status.player_moving and bot_status.player_direction == 'left':
        time.sleep(0.1)
        move_horizontal(MapPoint(up_point.x+3, p.y, 2))
        time.sleep(0.2)
    elif next_platform.end_x - up_point.x <= 10 and bot_status.player_moving and bot_status.player_direction == 'right':
        time.sleep(0.1)
        move_horizontal(MapPoint(up_point.x-3, p.y, 2))
        time.sleep(0.2)
        
    if dy < 5:
        press(Keybindings.JUMP)
    elif dy < Jump_Up.move_range.stop:
        Jump_Up(target).execute()
    else:
        RopeLift(target.y).execute()


@bot_status.run_if_enabled
def move_down(target: MapPoint):
    sleep_in_the_air(n=4)
    if target.y <= bot_status.player_pos.y:
        return
    next_p = MapPoint(bot_status.player_pos.x, target.y, 3)
    if shared_map.on_the_platform(next_p):
        Fall().execute()
    else:
        DoubleJump(target, False)


#########################
#        Y轴移动         #
#########################

class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    cooldown = 0.6
    backswing = 0
    move_range = range(26, 33)
    # 18-40

    def __init__(self, target: MapPoint, attack_if_needed=False):
        super().__init__(locals())
        self.target = target
        self.attack_if_needed = attack_if_needed

    def main(self, wait=True):
        while not self.canUse():
            utils.log_event("double jump waiting", bot_settings.debug)
            time.sleep(0.01)
        dx = self.target.x - bot_status.player_pos.x
        dy = self.target.y - bot_status.player_pos.y
        direction = 'left' if dx < 0 else 'right'
        start_y = bot_status.player_pos.y
        distance = abs(dx)

        self.__class__.castedTime = time.time()
        key_down(direction)
        time.sleep(0.02)
        if dy < 0 or not shared_map.is_continuous(bot_status.player_pos, self.target):
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.05)
            press(self.key, 1 if abs(dx) < 30 else 2, down_time=0.03, up_time=0.03)
        elif distance in range(32, 35):
            press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            press_acc(self.key, 2, down_time=0.03, up_time=0.04)
        elif distance <= 25:
            times = [0.02, 0.02, 0.02, 0.02]
            if distance in range(23, 26):
                times = [0.2, 0.2, 0.1, 0.1]
            elif distance in range(21, 23):
                times = [0.1, 0.25, 0.1, 0.02]
            elif distance in range(19, 21):
                times = [0.1, 0.2, 0.1, 0.02]
            elif distance == 18:
                times = [0.15, 0.12, 0.1, 0.02]
            elif distance == 17:
                times = [0.2, 0.1, 0.1, 0.02]
            elif distance == 16:
                times = [0.1, 0.1, 0.1, 0.02]
            elif distance == 15:
                times = [0.2, 0.05, 0.1, 0.02]
            elif distance == 10:
                times = [0.2, 0.02, 0.02, 0.02]
            elif distance in range(8, 10):
                times = [0.1, 0.02, 0.02, 0.02]
            elif distance == 7:
                times = [0.01, 0.02, 0.02, 0.01]
            press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=times[0])
            press_acc(self.key, 1, down_time=0.02, up_time=times[1])
            key_up(direction)
            time.sleep(0.02)
            press_acc(opposite_direction(direction), down_time=times[2], up_time=times[3])
            press(self.key, 1, down_time=0.02, up_time=0.02)
            self.attack_if_needed = False
        else:
            press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            press(self.key, 1, down_time=0.02, up_time=0.02)
        if self.attack_if_needed and self.target.y >= start_y:
            press(Keybindings.Quintuple_Star, down_time=0.01, up_time=0.1)
        key_up(direction)
        # if abs(shared_map.current_map.base_floor - start_y) <= 2:
        #     print("bingo")
        #     time.sleep(0.01)
        # else:
        sleep_in_the_air(n=2)
        return True


# 上跳
class Jump_Up(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    move_range = range(0, 29)

    def __init__(self, target: MapPoint):
        super().__init__(locals())
        self.target = target

    def main(self, wait=True):
        sleep_in_the_air(n=4)
        # time.sleep(0.2)
        # if bot_status.player_moving:
        #     press(opposite_direction(bot_status.player_direction))
        # evade_rope(True)

        dy = bot_status.player_pos.y - self.target.y
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.3)
        press(Keybindings.JUMP)
        time.sleep(1)
        sleep_in_the_air(n=10, detect_rope=True)
        time.sleep(0.1)
        key_up('up')
        return True

#########################
#        X轴移动         #
#########################


class Shadow_Dodge(Skill):
    key = Keybindings.Shadow_Dodge
    type = SkillType.Move
    cooldown = 0
    precast = 0
    backswing = 0.3
    move_range = range(11, 15)
    # 12-14

    def __init__(self, direction='right'):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if not self.canUse():
            return False

        self.__class__.castedTime = time.time()
        press(opposite_direction(self.direction), down_time=0.1)
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        # press(self.direction)
        sleep_in_the_air()
        return True

#######################
#       Summon        #
#######################


class Greater_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Summon
    cooldown = 60
    precast = 0.5
    backswing = 0.5
    duration = 55
    tolerance = 1

    def main(self, wait=True):
        while not self.canUse():
            Shadow_Attack().execute()
        Dark_Omen().execute()
        return super().main(wait)


class Replace_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Move
    cooldown = 3
    backswing = 1

    def __init__(self, resummon='False'):
        super().__init__(locals())
        self.resummon = bot_settings.validate_boolean(resummon)

    def main(self, wait=True):
        if not self.canUse():
            return False
        if self.resummon:
            key_down('down')
            time.sleep(0.01)
        result = super().main(wait)
        if self.resummon:
            key_up('down')
            time.sleep(0.01)
        return result


#######################
#       Skills        #
#######################

class Shadow_Bat(Skill):
    key = Keybindings.Shadow_Bat
    type = SkillType.Switch
    cooldown = 1
    ready = False


class Dark_Elemental(Skill):
    key = Keybindings.Dark_Elemental
    type = SkillType.Switch
    cooldown = 1
    ready = False


class Darkness_Ascending(Skill):
    key = Keybindings.Darkness_Ascending
    type = SkillType.Buff
    cooldown = 1800
    ready = False


class Quintuple_Star(Skill):
    key = Keybindings.Quintuple_Star
    type = SkillType.Attack
    backswing = 0.55


class Dark_Omen(Skill):
    key = Keybindings.Dark_Omen
    type = SkillType.Attack
    cooldown = 20
    backswing = 0.9
    tolerance = 1


class Shadow_Bite(Skill):
    key = Keybindings.Shadow_Bite
    type = SkillType.Attack
    cooldown = 15
    backswing = 0.7
    tolerance = 0.9

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        last_state = cls.ready
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.98)
        cls.ready = len(matchs) > 0
        if not cls.ready or cls.ready != last_state:
            cls.update_time = time.time()


class Dominion(Skill):
    key = Keybindings.Dominion
    type = SkillType.Attack
    cooldown = 175
    precast = 0.1
    backswing = 0.1
    tolerance = 5

    def main(self, wait=True):
        if not self.canUse():
            return False
        self.__class__.castedTime = time.time()
        press(self.__class__.key, down_time=self.__class__.precast, up_time=self.__class__.backswing)
        Shadow_Dodge().execute()
        return True


class Phalanx_Charge(Skill):
    key = Keybindings.Phalanx_Charge
    type = SkillType.Attack
    cooldown = 30
    precast = 0.1
    backswing = 0.75
    tolerance = 0.5

    def __init__(self, direction='none'):
        super().__init__(locals())
        if direction == 'none' or direction == None:
            self.direction = None
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if not self.canUse():
            return False
        if self.direction is not None:
            Direction(self.direction).execute()
        return super().main(wait)


class Silence(Skill):
    key = Keybindings.Silence
    type = SkillType.Attack
    cooldown = 350
    precast = 0.3
    backswing = 3
    tolerance = 6


class Rapid_Throw(Skill):
    key = Keybindings.Rapid_Throw
    type = SkillType.Attack
    cooldown = 90
    precast = 0.5
    backswing = 2
    tolerance = 5

    def main(self, wait=True):
        if not self.canUse():
            return False
        time.sleep(self.precast)
        self.castedTime = time.time()
        for _ in range(0, 10):
            press(self.key)
            time.sleep(0.3)
        time.sleep(self.backswing)
        return True


class Cygnus_Knights_Will(Command):
    key = Keybindings.Cygnus_Knights_Will
    type = SkillType.Buff
    cooldown = 300
    precast = 0.3
    backswing = 0.6
    tolerance = 5


class Attack(Command):
    key = Quintuple_Star.key
    type = SkillType.Attack
    backswing = Quintuple_Star.backswing

    def main(self, wait=True):
        return Quintuple_Star(wait).execute()


class Shadow_Attack(Command):
    cooldown = 4

    def __init__(self, direction=None):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)
        if self.direction is None:
            self.direction = 'right' if random() <= 0.5 else 'left'

    def main(self, wait=True):
        assert (shared_map.current_map)
        if not self.canUse() and not bot_status.elite_boss_detected:
            time.sleep(0.3)
            return False

        if bot_status.elite_boss_detected:
            Direction(opposite_direction(self.direction)).execute()
            burst().execute()

        start_time = time.time()
        if start_time - Shadow_Bite.castedTime > 5.5 and not bot_status.elite_boss_detected:
            while not Shadow_Bite.canUse():
                time.sleep(0.1)
                mobs = detect_mobs(capture.frame, MobType.NORMAL, True)
                if len(mobs) <= 2:
                    return False
                if time.time() - start_time > 2:
                    break

        n = 2
        self.__class__.castedTime = time.time()
        if Shadow_Bite.canUse():
            Shadow_Bite().execute()
        elif Silence.canUse():
            Silence().execute()
        elif Dominion.canUse():
            Dominion().execute()
        elif Arachnid.canUse():
            Arachnid().execute()
        elif SolarCrest.canUse():
            SolarCrest().execute()
        elif Dark_Omen.canUse():
            Dark_Omen().execute()
            n = 3
        else:
            n = 3 if bot_status.elite_boss_detected else 0
            self.__class__.castedTime = time.time() - 4

        if n > 0:
            if self.direction == 'right':
                Phalanx_Charge('left').execute()
                Direction("left" if bot_status.elite_boss_detected else "right").execute()
            else:
                Phalanx_Charge('right').execute()
                Direction("right" if bot_status.elite_boss_detected else "left").execute()
            key_down(Keybindings.Quintuple_Star)
            time.sleep(n)
            key_up(Keybindings.Quintuple_Star)
            time.sleep(Quintuple_Star.backswing)
        else:
            time.sleep(0.3)
        return True


class burst(Command):
    def main(self, wait=True):
        Shadow_Spear().execute()
        Shadow_Illusion().execute()
        if time.time() - self.castedTime > 30:
            Replace_Dark_Servant(resummon='True').execute()
        Shadow_Bite().execute()
        Silence().execute()
        Quintuple_Star().execute()
        Rapid_Throw().execute()
        self.castedTime = time.time()
        return True


class Detect_Around_Anchor(Command):
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
        if self.x == 0 and self.y == 0:
            anchor = bot_helper.locate_player_fullscreen(accurate=True)
        else:
            anchor = (self.x, self.y)

        if bot_helper.check_blind():
            # chat_bot.send_message("blind", capture.frame)
            if Cygnus_Knights_Will.canUse():
                Cygnus_Knights_Will().execute()
            elif Will_of_Erda.canUse():
                Will_of_Erda().execute()

        start = time.time()
        while True:
            mobs = detect_mobs_around_anchor(
                anchor=anchor,
                insets=AreaInsets(
                    top=self.top, bottom=self.bottom, left=self.left, right=self.right),
                multy_match=self.count > 1,
                debug=False)
            utils.log_event(f"mobs count = {len(mobs)}", bot_settings.debug)
            if len(mobs) >= self.count or bot_status.elite_boss_detected:
                break
            if time.time() - start > 7:
                utils.log_event("Detect_Around_Anchor timeout", bot_settings.debug)
                break
            time.sleep(0.3)
        return True

###################
#      Buffs      #
###################


class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            Dark_Elemental,
            Shadow_Bat,
            Transcendent_Cygnus_Blessing,
            LastResort,
            Glory_of_the_Guardians,
            Shadow_Spear,
            # Shadow_Illusion,
            ForTheGuild,
            HardHitter,
            Darkness_Ascending
        ]

        ForTheGuild.key = Keybindings.FOR_THE_GUILD
        HardHitter.key = Keybindings.HARD_HITTER
        LastResort.key = Keybindings.LAST_RESORT

        Arachnid.key = Keybindings.ARACHNID
        SolarCrest.key = Keybindings.SolarCrest

    def main(self, wait=True):
        for buff in self.buffs:
            if buff.canUse():
                utils.log_event(str(buff), bot_settings.debug)
                result = buff().main(wait)
                if result:
                    return True
        return False


class Transcendent_Cygnus_Blessing(Skill):
    key = Keybindings.Transcendent_Cygnus_Blessing
    type = SkillType.Buff
    cooldown = 240
    precast = 0.3
    backswing = 0.85

    @classmethod
    def load(cls):
        module_name = cls.__module__.split('.')[-1]
        path1 = f'assets/skills/{module_name}/{cls.__name__}.png'
        cls.icon = cv2.imread(path1, 0)
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
                capture.skill_frame, cls.icon[2:-2, 8:-2], threshold=0.9, debug=False)
            cls.ready = len(matchs) > 0

    @classmethod
    def check_buff_enabled(cls):
        matchs = utils.multi_match(
            capture.buff_frame, cls.icon[:14, 8:-8], threshold=0.9)
        if not matchs:
            matchs = utils.multi_match(
                capture.buff_frame, cls.icon[-14:, 8:-8], threshold=0.9)
        cls.enabled = len(matchs) > 0


class Glory_of_the_Guardians(Skill):
    key = Keybindings.Glory_of_the_Guardians
    type = SkillType.Buff
    cooldown = 120
    backswing = 0.75


class Shadow_Spear(Skill):
    key = Keybindings.Shadow_Spear
    type = SkillType.Buff
    cooldown = 177
    backswing = 0.6


class Shadow_Illusion(Skill):
    key = Keybindings.Shadow_Illusion
    type = SkillType.Buff
    cooldown = 180
    backswing = 0.75


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

        GOLD_POTION.key = Keybindings.GOLD_POTION
        CANDIED_APPLE.key = Keybindings.CANDIED_APPLE
        GUILD_POTION.key = Keybindings.GUILD_POTION
        LEGION_WEALTHY.key = Keybindings.LEGION_WEALTHY
        EXP_COUPON.key = Keybindings.EXP_COUPON
        Wealth_Potion.key = Keybindings.WEALTH_POTION
        EXP_Potion.key = Keybindings.EXP_POTION

    def main(self, wait=True):
        if bot_status.invisible:
            return False
        for potion in self.potions:
            if potion.canUse():
                potion().execute()
                time.sleep(0.2)
        return True


@bot_status.run_if_enabled
def find_next_point(start: MapPoint, target: MapPoint):
    utils.log_event(f"[find_next_point] start:{start.tuple} target:{str(target)}", bot_settings.debug)

    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        return target

    if target_reached(start, target):
        return

    start = shared_map.fixed_point(start)
    d_x = target.x - start.x
    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return

    if platform_start == platform_target:
        return target

    paths = shared_map.path_between(platform_start, platform_target)
    utils.log_event(f"[find_next_point] paths:", bot_settings.debug)
    if paths:
        for plat in paths:
            utils.log_event(f"  {str(plat)}", bot_settings.debug)
        next_platform = paths[1]
        d_y = next_platform.y - platform_start.y

        tmp_p = next_platform.center
        if len(paths) == 2:
            tmp_p = target
        if d_y == 0:
            next_p = find_next_horizontal_point(start, tmp_p)
            if next_p:
                return next_p
        elif d_y < 0:
            next_p = find_next_upper_point(start, tmp_p)
            if next_p:
                return next_p
        else:
            next_p = find_next_under_point(start, tmp_p)
            if next_p:
                return next_p
    return shared_map.platform_point(MapPoint(target.x, target.y - 1, 3))


def find_next_horizontal_point(start: MapPoint, target: MapPoint):
    if start.y != target.y:
        return

    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return
    if platform_start == platform_target:
        return target

    max_distance = 32
    target_range = None
    if platform_start.end_x < platform_target.begin_x:
        target_range = range(platform_target.begin_x + 3 - max_distance, platform_start.end_x + 1)
    else:
        target_range = range(platform_start.begin_x, platform_target.end_x - 3 + max_distance + 1)
    if start.x in target_range:
        return target
    else:
        target_x = (target_range.start + target_range.stop) / 2
        tolerance = (target_range.stop - target_range.start) / 2
        return MapPoint(int(target_x), start.y, int(tolerance))


def find_next_upper_point(start: MapPoint, target: MapPoint):
    if start.y <= target.y:
        return

    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return

    gap = platform_gap(platform_start, platform_target)
    if gap == -1:
        # 有交集
        # 优先垂直方向接近
        next_p = MapPoint(start.x, platform_target.y, 2)
        if not shared_map.is_continuous(next_p, target):
            next_p = None
        if next_p:
            if target_reached(start, next_p):
                return target
            else:
                return next_p

        # 尝试水平方向接近
        next_p = MapPoint(target.x, start.y, 2)
        if not shared_map.is_continuous(start, next_p):
            next_p = None
        if next_p:
            if target_reached(start, next_p):
                return target
            else:
                return next_p

        intersection_point = shared_map.point_of_intersection(platform_start, platform_target)
        assert (intersection_point)
        if target_reached(start, intersection_point):
            return target
        else:
            return intersection_point
    else:
        # 二段跳范围内
        if platform_start.end_x < platform_target.begin_x:
            next_p = MapPoint(platform_start.end_x - 2, platform_start.y, 3)
        else:
            next_p = MapPoint(platform_start.begin_x + 2, platform_start.y, 3)
        if target_reached(start, next_p):
            return target
        else:
            return next_p


def find_next_under_point(start: MapPoint, target: MapPoint):
    if start.y >= target.y:
        return

    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)

    if not platform_start or not platform_target:
        return

    gap = platform_gap(platform_start, platform_target)

    if not platform_start or not platform_target:
        return

    if gap == -1:
        next_p = MapPoint(start.x, platform_target.y, 3)
        if shared_map.on_the_platform(next_p):
            return next_p
        else:
            return shared_map.point_of_intersection(platform_start, platform_target)
    else:
        if platform_start.end_x < platform_target.begin_x:
            next_p = MapPoint(platform_start.end_x - 2, platform_start.y, 2)
        else:
            next_p = MapPoint(platform_start.begin_x + 2, platform_start.y, 2)
        if target_reached(start, next_p):
            return target
        else:
            return next_p


class Test_Command(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    backswing = 0.1

    def main(self, wait=True):
        for _ in range(0, 4):
            print('start:' + str(bot_status.player_pos.tuple))
            direction = 'right'
            key_down(direction)
            time.sleep(0.02)

            # 三段跳 40-41
            # press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.15)
            # press_acc(self.key, 2, down_time=0.1, up_time=0.03)

            # 二段跳 26-29
            # press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            # press(self.key, 1, down_time=0.02, up_time=0.02)

            # 急停
            # 23-25
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.2)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.1)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)

            # press(Keybindings.Quintuple_Star, down_time=0.01, up_time=0.02)

            key_up(direction)
            sleep_in_the_air(n=3)
            print('end: ' + str(bot_status.player_pos.tuple))
        return True

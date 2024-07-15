"""A collection of all commands that Night Lord can use to interact with the game. 	"""

from src.common import bot_status, bot_settings, utils
import time
from src.routine.components import *
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc
from src.command.commands import * # type: ignore


# List of key mappings
class Keybindings(DefaultKeybindings):
    # Movement
    JUMP = 's'
    FLASH_JUMP = ';'
    SHADOW_LEAP = 'a'
    SHADOW_SURGE = 'g'
    ROPE_LIFT = 'b'
    Go_Ardentmill = '='

    # Buffs
    GODDESS_BLESSING = '1'
    LAST_RESORT = '2'
    EPIC_ADVENTURE = '3'
    MEMORIES = '4'
    SHADOW_WALKER = 'shift'
    THROW_BLASTING = 'v'
    Throwing_Star_Barrage_Master = 'z'
    MARK = 'f1'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = ""
    GUILD_POTION = ""
    CANDIED_APPLE = '6'
    LEGION_WEALTHY = '='
    EXP_COUPON = ''

    # Skills
    SHOW_DOWN = 'd'
    SUDDEN_RAID = 'r'
    OMEN = 'x'
    ARACHNID = 'q'
    SHURIKEN = 'c'
    DARK_FLARE = 'w'
    ERDA_SHOWER = '`'


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
    elif distance >= ShadowSurge.move_range.start and ShadowSurge.ready:
        ShadowSurge('left' if d_x < 0 else 'right').execute()
    else:
        Walk(target).execute()


#########################
#        Y轴移动         #
#########################


@bot_status.run_if_enabled
def move_up(target):
    p = bot_status.player_pos
    dy = abs(p.y - target.y)

    up_point = MapPoint(p.x, target.y)
    if not shared_map.is_continuous(up_point, target):
        # 跨平台
        DoubleJump(target, False)
        return

    next_platform = shared_map.platform_of_point(target)
    assert (next_platform)
    if bot_status.player_moving and bot_status.player_direction == 'left':
        if up_point.x - next_platform.begin_x <= 8:
            move_horizontal(MapPoint(up_point.x+3, p.y, 2))
        else:
            time.sleep(0.2)
    elif bot_status.player_moving and bot_status.player_direction == 'right':
        if next_platform.end_x - up_point.x <= 10:
            move_horizontal(MapPoint(up_point.x-3, p.y, 2))
        else:
            time.sleep(0.2)

    if dy < 5:
        press(Keybindings.JUMP)
    elif dy <= 18:
        ShadowLeap(True if dy > 15 else False).execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    sleep_in_the_air(n=4)
    if target.y <= bot_status.player_pos.y:
        return
    if abs(bot_status.player_pos.y - target.y) <= 4:
        sleep_in_the_air()
        return
    next_p = MapPoint(bot_status.player_pos.x, target.y, 3)
    if shared_map.on_the_platform(next_p):
        Fall().execute()
    else:
        DoubleJump(target, False)


class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.FLASH_JUMP
    type = SkillType.Move
    cooldown = 0.6
    backswing = 0
    move_range = range(26, 33)

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
        start_p = bot_status.player_pos
        start_y = bot_status.player_pos.y

        self.__class__.castedTime = time.time()
        key_down(direction)
        time.sleep(0.02)
        need_check = True
        if dy < 0 or not shared_map.is_continuous(bot_status.player_pos, self.target):
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.05)
            press(self.key, 1 if abs(dx) < 30 else 2, down_time=0.03, up_time=0.03)
            self.attack_if_needed = False
        else:
            need_check = False
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.02)
            press(self.key, 1, down_time=0.02, up_time=0.03)
        if self.attack_if_needed:
            Attack().execute()
            time.sleep(0.1)
        key_up(direction)
        sleep_in_the_air(n=1)

        if need_check and not target_reached(bot_status.player_pos, self.target):
            utils.log_event(
                f"[Failed][DoubleJump] start={start_p.tuple} end={bot_status.player_pos.tuple} target={str(self.target)}", True)
        return True


# 上跳
class ShadowLeap(Command):
    key = Keybindings.SHADOW_LEAP
    type = SkillType.Move
    precast = 0.03
    backswing = 0.9

    def __init__(self, jump: bool = False):
        super().__init__(locals())
        self.jump = jump

    def main(self, wait=True):
        time.sleep(self.__class__.precast)
        if self.jump:
            press_acc(Keybindings.JUMP, down_time=0.05, up_time=0.06)

        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        return True


# 水平位移
class ShadowSurge(Skill):
    key = Keybindings.SHADOW_SURGE
    type = SkillType.Move
    cooldown = 5
    precast = 0
    backswing = 0.18
    move_range = range(10, 15)

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if not self.canUse():
            return False

        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        key_down(self.direction)
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        key_up(self.direction)
        return True

#######################
#       Summon        #
#######################


class DarkFlare(Skill):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    key = Keybindings.DARK_FLARE
    type = SkillType.Summon
    cooldown = 58
    backswing = 0.8
    duration = 60

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if self.direction is not None:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        return super().main()


#######################
#       Skills        #
#######################

class Mark(Skill):
    key = Keybindings.MARK
    type = SkillType.Switch
    cooldown = 1
    ready = False


class ShowDown(Command):
    key = Keybindings.SHOW_DOWN
    type = SkillType.Attack
    backswing = 0.5

    def main(self, wait=True):
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        return True

class Attack(Command):
    key = ShowDown.key
    type = SkillType.Attack
    backswing = ShowDown.backswing

    def __init__(self, detect=False):
        super().__init__(locals())
        self.detect = bot_settings.validate_boolean(detect)

    def main(self, wait=True):
        if self.detect:
            pos = (800, 560)
            if bot_status.player_direction == 'left':
                mobs = detect_mobs_around_anchor(
                    anchor=pos, insets=AreaInsets(top=200, bottom=100, left=300, right=0))
            else:
                mobs = detect_mobs_around_anchor(
                    anchor=pos, insets=AreaInsets(top=200, bottom=100, left=0, right=300))
            if len(mobs) > 0:
                ShowDown().execute()
        else:
            ShowDown().execute()
        return True


class SuddenRaid(Skill):
    key = Keybindings.SUDDEN_RAID
    type = SkillType.Attack
    cooldown = 30
    backswing = 0.75

    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        usable = super().canUse()
        if usable:
            mobs = detect_mobs(capture.frame)
            return mobs is None or len(mobs) > 0
        else:
            return False

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[9:, ], threshold=0.9, debug=False)
        cls.ready = len(matchs) > 0


class Omen(Skill):
    key = Keybindings.OMEN
    type = SkillType.Buff
    cooldown = 60
    backswing = 0.8


class Shurrikane(Command):
    key = Keybindings.SHURIKEN
    type = SkillType.Attack
    cooldown = 23
    backswing = 0.35

    def __init__(self, stop: float = 0):
        super().__init__(locals())
        self.stop = stop

    def main(self, wait=True):
        if not self.canUse():
            return False
        self.__class__.castedTime = time.time()
        press(self.__class__.key, up_time=0)
        if self.stop > 0:
            time.sleep(self.stop)
            press(self.__class__.key, up_time=0)
            time.sleep(max(self.__class__.backswing - self.stop, 0))
        else:
            time.sleep(self.__class__.backswing)
        return True

###################
#      Buffs      #
###################

class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            Mark,
            MapleWarrior,
            MapleWorldGoddessBlessing,
            LastResort,
            ForTheGuild,
            HardHitter,
            ShadowWalker,
            ThrowBlasting,
        ]
        
        ForTheGuild.key = Keybindings.FOR_THE_GUILD
        HardHitter.key = Keybindings.HARD_HITTER
        LastResort.key = Keybindings.LAST_RESORT

        Arachnid.key = Keybindings.ARACHNID
        SolarCrest.key = Keybindings.SolarCrest

    def main(self, wait=True):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!use buff")
        for buff in self.buffs:
            if buff.canUse():
                print(buff)
                result = buff().main(wait)
                if result:
                    return True
        return False


class Memories(Skill):
    key = Keybindings.MEMORIES
    cooldown = 180
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff


class EPIC_ADVENTURE(Skill):
    key = Keybindings.EPIC_ADVENTURE
    type = SkillType.Buff
    cooldown = 120
    backswing = 0.75


class ShadowWalker(Skill):
    key = Keybindings.SHADOW_WALKER
    type = SkillType.Buff
    cooldown = 180
    precast = 0.3
    backswing = 0.8


class ThrowBlasting(Skill):
    key = Keybindings.THROW_BLASTING
    type = SkillType.Buff
    cooldown = 180
    backswing = 0.8

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        if capture.frame is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[8:, ], threshold=0.95)
        cls.ready = len(matchs) > 0

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
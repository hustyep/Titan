"""A collection of all commands that Night Lord can use to interact with the game. 	"""

from src.common import bot_status, bot_settings, utils
import time
from src.routine.components import *
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc
from src.command.commands import *


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

    # SHADOW_PARTNER = '3'
    # SPEED_INFUSION = '8'
    # HOLY_SYMBOL = '4'
    # SHARP_EYE = '5'
    # COMBAT_ORDERS = '6'
    # ADVANCED_BLESSING = '7'

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
def step(target, tolerance):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    d_x = target[0] - bot_status.player_pos[0]
    d_y = target[1] - bot_status.player_pos[1]
    if abs(d_x) >= 26:
        hit_and_run('right' if d_x > 0 else 'left', target, tolerance)
        return

    next_p = find_next_point(bot_status.player_pos, target, tolerance)
    print(f"next_p:{next_p}")
    if not next_p:
        return

    bot_status.path = [bot_status.player_pos, next_p, target]

    d_x = next_p[0] - bot_status.player_pos[0]
    d_y = next_p[1] - bot_status.player_pos[1]

    direction = None
    if abs(d_x) > tolerance:
        direction = 'right' if d_x > 0 else 'left'
    else:
        direction = 'down' if d_y > 0 else 'up'

    if direction == "up":
        move_up(next_p)
    elif direction == "down":
        move_down(next_p)
    elif abs(d_x) >= 24:
        hit_and_run(direction, next_p, tolerance)
    elif abs(d_x) >= 10 and ShadowSurge.ready:
        ShadowSurge(direction).execute()
        # Attack().execute()
    else:
        Walk(target_x=next_p[0], tolerance=tolerance).execute()


@bot_status.run_if_enabled
def hit_and_run(direction, target, tolerance):
    if gui_setting.detection.detect_mob:
        if gui_setting.detection.detect_elite or gui_setting.detection.detect_boss:
            t = AsyncTask(target=pre_detect, args=(direction,))
            t.start()
            elite_detected = t.join()
            DoubleJump(target=target, attack_if_needed=True).execute()
            if elite_detected:
                pass
        else:
            DoubleJump(target=target, attack_if_needed=True).execute()
    else:
        DoubleJump(target=target, attack_if_needed=True).execute()

#########################
#        Y轴移动         #
#########################


@bot_status.run_if_enabled
def move_up(target):
    p = bot_status.player_pos
    dy = abs(p[1] - target[1])

    if dy <= 6:
        press(Keybindings.JUMP)
    elif dy <= 18:
        ShadowLeap(True if dy > 15 else False).execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    sleep_in_the_air(n=1)
    if target[1] > bot_status.player_pos[1]:
        Fall().execute()


class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.FLASH_JUMP
    type = SkillType.Move
    # cooldown = 0.1

    def __init__(self, target: tuple[int, int], attack_if_needed=False):
        super().__init__(locals())

        self.target = target
        self.attack_if_needed = attack_if_needed

    def detect_mob(self, direction):
        insets = AreaInsets(top=220,
                            bottom=100,
                            left=650 if direction == 'left' else 10,
                            right=10 if direction == 'left' else 600)
        anchor = capture.locate_player_fullscreen(accurate=True)
        mobs = detect_mobs(insets=insets, anchor=anchor)
        return mobs

    def main(self):
        while not self.canUse():
            time.sleep(0.01)
        dx = self.target[0] - bot_status.player_pos[0]
        dy = self.target[1] - bot_status.player_pos[1]
        direction = 'left' if dx < 0 else 'right'
        start_y = bot_status.player_pos[1]

        self.__class__.castedTime = time.time()
        key_down(direction)
        if self.attack_if_needed:
            # detect = AsyncTask(
            #     target=self.detect_mob, args=(direction, ))
            # detect.start()
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.02)
            # mobs_detected = detect.join()
            mobs_detected = True
            times = 2 if mobs_detected else 1
            press(self.key, 1, down_time=0.02, up_time=0.03)
            if mobs_detected:
                Attack().execute()
        else:
            times = 2 if abs(dx) >= 32 else 1
            if dy == 0:
                if abs(dx) in range(20, 26):
                    press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.5)
                else:
                    press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            else:
                press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.05)
            press(self.key, times, down_time=0.03, up_time=0.03)

        key_up(direction)
        if start_y == 68:
            time.sleep(0.015)
        else:
            sleep_in_the_air(n=1, start_y=start_y)


# 上跳
class ShadowLeap(Command):
    key = Keybindings.SHADOW_LEAP
    type = SkillType.Move
    precast = 0.03
    backswing = 0.9

    def __init__(self, jump: bool = False):
        super().__init__(locals())
        self.jump = jump

    def main(self):
        time.sleep(self.__class__.precast)
        if self.jump:
            press_acc(Keybindings.JUMP, down_time=0.05, up_time=0.06)

        press_acc(self.__class__.key, up_time=self.__class__.backswing)


# 水平位移
class ShadowSurge(Skill):
    key = Keybindings.SHADOW_SURGE
    type = SkillType.Move
    cooldown = 5
    precast = 0
    backswing = 0.18

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
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

    def main(self):
        if self.direction is not None:
            press_acc(self.direction, down_time=0.03, up_time=0.03)
        super().main()


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

    def main(self):
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)


class Attack(Command):
    key = ShowDown.key
    type = SkillType.Attack
    backswing = ShowDown.backswing
    
    def __init__(self, detect = False):
        super().__init__(locals())
        self.detect = bot_settings.validate_boolean(detect)
        
    def main(self):
        if self.detect:
            pos = (800, 560)
            if bot_status.player_direction == 'left':
                mobs = detect_mobs(
                    anchor=pos, insets=AreaInsets(top=200, bottom=100, left=300, right=0))
            else:
                mobs = detect_mobs(
                    anchor=pos, insets=AreaInsets(top=200, bottom=100, left=0, right=300))
            if len(mobs) > 0:
                ShowDown().execute()
        else:
            ShowDown().execute()


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

    def __init__(self, stop: float = None):
        super().__init__(locals())
        self.stop = stop

    def main(self):
        if not self.canUse():
            return
        self.__class__.castedTime = time.time()
        press(self.__class__.key, up_time=0)
        if self.stop is not None and self.stop != 'None':
            time.sleep(self.stop)
            press(self.__class__.key, up_time=0)
            time.sleep(max(self.__class__.backswing - self.stop, 0))
        else:
            time.sleep(self.__class__.backswing)


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

    def main(self, wait=True):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!use buff")
        for buff in self.buffs:
            if buff.canUse():
                print(buff)
                result = buff().main(wait)
                if result:
                    break
    
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

"""A collection of all commands that Hero can use to interact with the game. 	"""

from src.common import bot_status, bot_settings, utils
import time
from src.routine.components import *
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc
from src.command.commands import *


# List of key mappings
class Keybindings(DefaultKeybindings):
    # Movement
    JUMP = 's'
    FLASH_JUMP = 's'
    Upward_Charge = 'a'
    Rush = 'r'
    ROPE_LIFT = 'b'
    Go_Ardentmill = '5'

    # Skills
    RagingBlow = 'f'
    Puncture = 'd'
    RisingRage = 'e'
    ARACHNID = 'q'
    BeamBlade = 'c'
    BurningSoulBlade = 'w'
    ERDA_SHOWER = '`'

    # Buffs
    EPIC_ADVENTURE = '3'
    MEMORIES = '4'
    CryValhalla = '1'
    InstinctualCombo = '2'
    Throwing_Star_Barrage_Master = 'z'
    ComboAttack = 'f1'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = ""
    GUILD_POTION = ""
    CANDIED_APPLE = '6'
    LEGION_WEALTHY = '='
    EXP_COUPON = ''

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
    if abs(d_x) >= 20:
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
        print("move_up")
    elif direction == "down":
        move_down(next_p)
        print("move_down")
    elif abs(d_x) >= 20:
        hit_and_run(direction, next_p, tolerance)
        print("hit_and_run")
    else:
        Walk(target_x=next_p[0], tolerance=tolerance).execute()
        print("Walk")


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

    if dy <= 3:
        sleep_in_the_air(n=4)
    elif dy <= 6:
        press(Keybindings.JUMP)
        sleep_in_the_air(n=4)
    elif dy <= 20:
        UpwardCharge(True if dy > 15 else False).execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    sleep_in_the_air(n=1)
    if target[1] > bot_status.player_pos[1]:
        Fall().execute()


class DoubleJump(Command):
    """Performs a flash jump in the given direction."""
    key = Keybindings.JUMP
    type = SkillType.Move
    cooldown = 0.35

    def __init__(self, target: tuple[int, int], attack_if_needed=False):
        super().__init__(locals())

        self.target = target
        self.attack_if_needed = attack_if_needed

    def detect_mob(self, direction):
        insets = AreaInsets(top=220,
                            bottom=100,
                            left=650 if direction == 'left' else 10,
                            right=10 if direction == 'left' else 600)
        anchor = bot_helper.locate_player_fullscreen(accurate=True)
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
            if start_y >= shared_map.current_map.base_floor - 15:
                press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.18)
                press(self.key, 1, down_time=0.02, up_time=0.03)
                Puncture().execute()
            else:
                press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.05)
                press(self.key, 1, down_time=0.02, up_time=0.03)
                RagingBlow().execute()
        else:
            if dy == 0:
                if abs(dx) in range(20, 26):
                    press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.5)
                else:
                    press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            else:
                press(Keybindings.JUMP, 1, down_time=0.05, up_time=0.05)
            press(self.key, 1, down_time=0.03, up_time=0.03)

        key_up(direction)
        if start_y == bot_settings.boundary_point_l[1]:
            time.sleep(0.015)
        else:
            sleep_in_the_air(n=1, start_y=start_y)


# 上跳
class UpwardCharge(Command):
    key = Keybindings.Upward_Charge
    type = SkillType.Move
    precast = 0.03
    backswing = 1

    def __init__(self, jump: bool = False):
        super().__init__(locals())
        self.jump = jump

    def main(self):
        time.sleep(self.__class__.precast)
        if self.jump:
            press_acc(Keybindings.JUMP, down_time=0.05, up_time=0.06)

        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        sleep_in_the_air(n=20)

# 水平位移


class Rush(Skill):
    key = Keybindings.Rush
    type = SkillType.Move
    cooldown = 5
    precast = 0
    backswing = 0.8

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        if not self.canUse():
            return False

        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        Direction(self.direction).execute()
        press(self.key)
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        return True

#######################
#       Summon        #
#######################


class BurningSoulBlade(Skill):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    key = Keybindings.BurningSoulBlade
    type = SkillType.Summon
    cooldown = 118
    backswing = 1.3
    duration = 75

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
            capture.skill_frame, cls.icon[10:, : -15], threshold=0.94, debug=False)
        cls.ready = len(matchs) > 0

    def main(self):
        if not self.canUse():
            return
        if self.direction:
            Direction(self.direction).execute()
        time.sleep(0.3)
        press(Keybindings.BurningSoulBlade, 1)
        self.__class__.castedTime = time.time()
        time.sleep(self.__class__.backswing)


#######################
#       Skills        #
#######################

class ComboAttack(Skill):
    key = Keybindings.ComboAttack
    type = SkillType.Switch
    cooldown = 1
    ready = False


class RagingBlow(Command):
    key = Keybindings.RagingBlow
    type = SkillType.Attack
    backswing = 0.2

    def main(self):
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)


class Puncture(Command):
    key = Keybindings.Puncture
    type = SkillType.Attack
    backswing = 0.6

    def main(self):
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)


class Attack(Command):
    key = Puncture.key
    type = SkillType.Attack
    backswing = Puncture.backswing

    def __init__(self, detect=False):
        super().__init__(locals())
        self.detect = bot_settings.validate_boolean(detect)

    def main(self):
        if self.detect:
            if bot_status.player_direction == 'left':
                mobs = detect_mobs_around_anchor(
                    anchor=bot_helper.locate_player_fullscreen(accurate=True),
                    insets=AreaInsets(top=200, bottom=100, left=300, right=0))
            else:
                mobs = detect_mobs_around_anchor(
                    anchor=bot_helper.locate_player_fullscreen(accurate=True),
                    insets=AreaInsets(top=200, bottom=100, left=0, right=300))
            if len(mobs) > 0:
                RagingBlow().execute()
        else:
            RagingBlow().execute()


class BeamBlade(Command):
    key = Keybindings.BeamBlade
    type = SkillType.Attack
    cooldown = 6
    backswing = 0.5

    def __init__(self, direction='up'):
        super().__init__(locals())
        self.direction = direction

    def main(self):
        if not self.canUse():
            return
        key_down(self.direction)
        time.sleep(0.03)
        self.__class__.castedTime = time.time()
        press(self.key)
        key_up(self.direction)
        time.sleep(self.backswing)


class RisingRage(Command):
    key = Keybindings.RisingRage
    type = SkillType.Attack
    cooldown = 10
    backswing = 1.2

    def __init__(self):
        super().__init__(locals())

    def main(self):
        if not self.canUse():
            return
        self.__class__.castedTime = time.time()
        press(self.__class__.key, up_time=0)
        time.sleep(self.__class__.backswing)

###################
#      Buffs      #
###################


class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            ComboAttack,
            # MapleWarrior,
            # MapleWorldGoddessBlessing,
            # ForTheGuild,
            # HardHitter,
        ]

    def main(self, wait=True):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!use buff")
        for buff in self.buffs:
            if buff.canUse():
                print(buff)
                result = buff().main(wait)
                if result:
                    break


class CryValhalla(Skill):
    key = Keybindings.CryValhalla
    type = SkillType.Buff
    cooldown = 120
    precast = 0.3
    backswing = 0.8


class InstinctualCombo(Skill):
    key = Keybindings.InstinctualCombo
    type = SkillType.Buff
    cooldown = 120
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

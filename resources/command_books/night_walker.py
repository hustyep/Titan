"""A collection of all commands that Night Walker can use to interact with the game. 	"""

from src.common import bot_status, bot_settings, utils
import time
from src.routine.components import *
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc
from src.command.commands import *


# List of key mappings
class Keybindings(DefaultKeybindings):
    # Movement
    JUMP = 's'
    Shadow_Jump = 'g'
    Shadow_Dodge = 'a'
    ROPE_LIFT = 'b'
    Go_Ardentmill = '='

    # Buffs
    Transcendent_Cygnus_Blessing = '1'
    Glory_of_the_Guardians = '2'
    LAST_RESORT = '3'
    Shadow_Illusion = '4'
    Shadow_Spear = 'v'
    Throwing_Star_Barrage_Master = 'z'
    Shadow_Bat = 'f1'
    Dark_Elemental = 'f2'
    Darkness_Ascending = '7'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = ""
    GUILD_POTION = ""
    CANDIED_APPLE = '6'
    LEGION_WEALTHY = '='
    EXP_COUPON = ''

    # Skills
    Quintuple_Star = 'f'
    Dark_Omen = 'r'
    OMEN = 'x'
    Dominion = 'c'
    ERDA_SHOWER = '`'
    Phalanx_Charge = 'z'
    Greater_Dark_Servant = 'd'
    Shadow_Bite = 'e'
    Rapid_Throw = 'x'
    Silence = ''

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
    elif abs(d_x) >= 10:
        Shadow_Dodge(direction).execute()
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
    elif dy <= 23:
        Jump_Up().execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    sleep_in_the_air(n=1)
    if target[1] > bot_status.player_pos[1]:
        Fall().execute()


class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.Shadow_Jump
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
            time.sleep(0.02)
        else:
            sleep_in_the_air(n=1, start_y=start_y)


# 上跳
class Jump_Up(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move

    def __init__(self, target):
        super().__init__(locals())
        self.target = target

    def main(self):
        # TODO too long
        time.sleep(0.5)

        target_left = (self.target[0] - 1, self.target[1])
        target_right = (self.target[0] + 1, self.target[1])
        if not shared_map.on_the_platform(target_left):
            press('right')
        elif not shared_map.on_the_platform(target_right):
            press('left')

        evade_rope(self.target)

        dy = bot_status.player_pos[1] - self.target[1]
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.1)
        press(self.key, 1)
        key_up('up')
        sleep_in_the_air(n=10)


# 水平位移
class Shadow_Dodge(Skill):
    key = Keybindings.Shadow_Dodge
    type = SkillType.Move
    cooldown = 0
    precast = 0
    backswing = 1.5

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        if not self.canUse():
            return False

        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        if self.direction == 'left':
            direction = 'right'
        else:
            direction = "left"
        key_down(direction)
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        key_up(direction)
        return True

#######################
#       Summon        #
#######################


class Greater_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Summon
    cooldown = 58
    backswing = 0.8
    duration = 60

    def __init__(self):
        super().__init__(locals())

    def main(self):
        super().main()


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
    type = SkillType.Switch
    cooldown = 1
    ready = False

class Quintuple_Star(Command):
    key = Keybindings.Quintuple_Star
    type = SkillType.Attack
    backswing = 0.5

    def main(self):
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)


class Attack(Command):
    key = Quintuple_Star.key
    type = SkillType.Attack
    backswing = Quintuple_Star.backswing

    def __init__(self, detect=False):
        super().__init__(locals())
        self.detect = bot_settings.validate_boolean(detect)

    def main(self):
        if self.detect:
            pos = (800, 560)
            if bot_status.player_direction == 'left':
                mobs = detect_mobs_around_anchor(
                    anchor=pos, insets=AreaInsets(top=200, bottom=100, left=300, right=0))
            else:
                mobs = detect_mobs_around_anchor(
                    anchor=pos, insets=AreaInsets(top=200, bottom=100, left=0, right=300))
            if len(mobs) > 0:
                Quintuple_Star().execute()
        else:
            Quintuple_Star().execute()


class Dark_Omen(Skill):
    key = Keybindings.Dark_Omen
    type = SkillType.Attack
    cooldown = 10
    backswing = 0.75

    @classmethod
    def check(cls):
        if cls.icon is None:
            return
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[9:, ], threshold=0.9, debug=False)
        cls.ready = len(matchs) > 0


class Shadow_Bite(Skill):
    key = Keybindings.Shadow_Bite
    type = SkillType.Attack
    cooldown = 15
    backswing = 0.5


class Shadow_Spear(Skill):
    key = Keybindings.Shadow_Spear
    type = SkillType.Buff
    cooldown = 177
    backswing = 0.6


class Dominion(Skill):
    key = Keybindings.Dominion
    type = SkillType.Buff
    cooldown = 180
    backswing = 1

class Phalanx_Charge(Skill):
    key = Keybindings.Phalanx_Charge
    type = SkillType.Attack
    cooldown = 30
    backswing = 0.75


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
        ]

    def main(self, wait=True):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!use buff")
        for buff in self.buffs:
            if buff.canUse():
                print(buff)
                result = buff().main(wait)
                if result:
                    break


class Transcendent_Cygnus_Blessing(Skill):
    key = Keybindings.Transcendent_Cygnus_Blessing
    type = SkillType.Buff
    cooldown = 240
    backswing = 0.75


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

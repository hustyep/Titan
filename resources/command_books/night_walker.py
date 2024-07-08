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

    utils.log_event(f"[step]target:{str(target)}", bot_settings.debug)
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
    elif distance >=15 or distance in range(7, 10):
        DoubleJump(target=target, attack_if_needed=False).execute()
    elif distance >= Shadow_Dodge.move_range.start:
        Shadow_Dodge('left' if d_x < 0 else 'right').execute()
    else:
        Walk(target).execute()


@bot_status.run_if_enabled
def move_up(target: MapPoint):
    p = bot_status.player_pos
    dy = abs(p.y - target.y)

    if dy < 5:
        press(Keybindings.JUMP)
    elif dy < Jump_Up.move_range.stop:
        Jump_Up(target).execute()
    else:
        RopeLift(target.y).execute()


@bot_status.run_if_enabled
def move_down(target: MapPoint):
    sleep_in_the_air(n=4)
    # evade_rope()
    if target.y > bot_status.player_pos.y:
        Fall().execute()


#########################
#        Y轴移动         #
#########################

class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    backswing = 0.1
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
        time.sleep(0.1)
        if dy < 0 or not shared_map.is_continuous(bot_status.player_pos, self.target):
            press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.05)
            press(self.key, 1 if abs(dx) < 30 else 2, down_time=0.03, up_time=0.03)
        elif distance in range(32, 35):
            press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
            press_acc(self.key, 2, down_time=0.03, up_time=0.04)
        elif distance <= 25:
            if distance in range(23, 26):
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
                press_acc(self.key, 1, down_time=0.02, up_time=0.2)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.1)
            elif distance in range(21, 23):
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.1)
                press_acc(self.key, 1, down_time=0.02, up_time=0.25)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            elif distance in range(19, 21):
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.1)
                press_acc(self.key, 1, down_time=0.02, up_time=0.2)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            elif distance == 18:
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.15)
                press(self.key, 1, down_time=0.02, up_time=0.12)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            elif distance == 17:
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
                press_acc(self.key, 1, down_time=0.02, up_time=0.1)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            elif distance == 16:
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.1)
                press_acc(self.key, 1, down_time=0.02, up_time=0.1)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            elif distance == 15:
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
                press_acc(self.key, 1, down_time=0.02, up_time=0.05)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            elif distance in range(8, 10):
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.03)
                press_acc(self.key, 1, down_time=0.02, up_time=0.02)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.02, up_time=0.02)
            elif distance == 7:
                press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
                press_acc(self.key, 1, down_time=0.02, up_time=0.02)
                key_up(direction)
                time.sleep(0.02)
                press_acc(opposite_direction(direction), down_time=0.02, up_time=0.01)
            press(self.key, 1, down_time=0.02, up_time=0.02)
            self.attack_if_needed = False
        else:
            press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            press(self.key, 1, down_time=0.02, up_time=0.02)
        if self.attack_if_needed and self.target.y >= start_y:
            press(Keybindings.Quintuple_Star, down_time=0.01, up_time=0.01)
        key_up(direction)
        # if abs(shared_map.current_map.base_floor - start_y) <= 2:
        #     print("bingo")
        #     time.sleep(0.01)
        # else:
        sleep_in_the_air(n=1)
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
        time.sleep(0.2)
        # if bot_status.player_moving:
        #     press(opposite_direction(bot_status.player_direction))
        # evade_rope(True)

        up_point = MapPoint(bot_status.player_pos.x, self.target.y)
        if not shared_map.on_the_platform(up_point, True) and shared_map.on_the_platform(MapPoint(self.target.x, bot_status.player_pos.y)):
            move_horizontal(
                MapPoint(self.target.x, bot_status.player_pos.y, 3))
        dy = bot_status.player_pos.y - self.target.y
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.3)
        press(Keybindings.JUMP, 1)
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
    move_range = range(10, 15)
    # 12-14

    def __init__(self, direction='right'):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self, wait=True):
        if not self.canUse():
            return False

        sleep_in_the_air(n=1)
        self.__class__.castedTime = time.time()
        press(opposite_direction(self.direction))
        press_acc(self.__class__.key, down_time=0.1, up_time=self.__class__.backswing)
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
    backswing = 0.8
    duration = 55
    tolerance = 1

    def main(self, wait=True):
        while not self.canUse():
            Shadow_Attack().execute()
        return super().main(wait)


class Replace_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Move
    cooldown = 3
    backswing = 1


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


class Attack(Command):
    key = Quintuple_Star.key
    type = SkillType.Attack
    backswing = Quintuple_Star.backswing

    def main(self, wait=True):
        return Quintuple_Star(wait).execute()


class Shadow_Attack(Command):
    cooldown = 4

    def main(self, wait=True):
        assert (shared_map.current_map)
        if not self.canUse() and not bot_status.elite_boss_detected:
            time.sleep(0.3)
            return False

        if bot_status.elite_boss_detected:
            burst().execute()

        start_time = time.time()
        if start_time - Shadow_Bite.castedTime > 5.7 and not bot_status.elite_boss_detected:
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
            n = 2.5
        elif Silence.canUse():
            Silence().execute()
            n = 1
        elif Dominion.canUse():
            Dominion().execute()
        elif Arachnid.canUse():
            Arachnid().execute()
        elif SolarCrest.canUse():
            SolarCrest().execute()
        elif Dark_Omen.canUse():
            Dark_Omen().execute()
            n = 4
        else:
            n = 3 if bot_status.elite_boss_detected else 0
            self.__class__.castedTime = time.time() - 4

        if n > 0:
            if shared_map.current_map.name == 'Outlaw-Infested Wastes 2':
                Phalanx_Charge('left').execute()
                Direction("left" if bot_status.elite_boss_detected else "right").execute()
            else:
                Phalanx_Charge('left').execute()
                Direction("right" if bot_status.elite_boss_detected else "right").execute()
            key_down(Keybindings.Quintuple_Star)
            time.sleep(n)
            key_up(Keybindings.Quintuple_Star)
            time.sleep(Quintuple_Star.backswing)
        else:
            time.sleep(0.3)
        return True


class burst(Command):
    def main(self, wait=True):
        Shadow_Illusion().execute()
        Shadow_Bite().execute()
        Silence().execute()
        Rapid_Throw().execute()
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
        start = time.time()
        while True:
            mobs = detect_mobs_around_anchor(
                anchor=anchor,
                insets=AreaInsets(
                    top=self.top, bottom=self.bottom, left=self.left, right=self.right),
                multy_match=self.count > 1,
                debug=False)
            utils.log_event(f"mobs count = {len(mobs)}", bot_settings.debug)
            if len(mobs) >= self.count:
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


class Test_Command(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    backswing = 0.1
    
    def main(self, wait=True):
        for _ in range(0, 4):
            direction = 'right'
            key_down(direction)
            time.sleep(0.1)

            # 三段跳 40-41
            # print('start:' + str(bot_status.player_pos.tuple))
            # press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.15)
            # press_acc(self.key, 2, down_time=0.1, up_time=0.03)

            # 三段跳 37-38
            # print('start:' + str(bot_status.player_pos.tuple))
            # press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.1)
            # press_acc(self.key, 2, down_time=0.1, up_time=0.03)

            # 三段跳 35-36
            # print('start:' + str(bot_status.player_pos.tuple))
            # press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.1)
            # press_acc(self.key, 2, down_time=0.06, up_time=0.03)
            
            # 三段跳 30-33
            # print('start:' + str(bot_status.player_pos.tuple))
            # press_acc(Keybindings.JUMP, 1, down_time=0.03, up_time=0.05)
            # press_acc(self.key, 2, down_time=0.03, up_time=0.03)

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
            
            # 21-22
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.1)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.25)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 19-20
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.1)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.2)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 18
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.15)
            # press(self.key, 1, down_time=0.02, up_time=0.12)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 17
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.1)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 16
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.1)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.1)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 15
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.2)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.05)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.1, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 8-9
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.03)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.02, up_time=0.02)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            
            # 7
            # press_acc(Keybindings.JUMP, 1, down_time=0.02, up_time=0.01)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)
            # key_up(direction)
            # time.sleep(0.02)
            # press_acc(opposite_direction(direction), down_time=0.02, up_time=0.01)
            # press_acc(self.key, 1, down_time=0.02, up_time=0.02)

            # press(Keybindings.Quintuple_Star, down_time=0.01, up_time=0.01)

            key_up(direction)
            sleep_in_the_air(n=2)
            print('end: ' + str(bot_status.player_pos.tuple))
        return True

@bot_status.run_if_enabled
def find_next_point(start: MapPoint, target: MapPoint):
    if shared_map.minimap_data is None or len(shared_map.minimap_data) == 0:
        return target

    if target_reached(start, target):
        return

    start = shared_map.fixed_point(start)
    d_x = target.x - start.x
    d_y = target.y - start.y

    if abs(d_x) <= target.tolerance:
        return target

    platform_start = shared_map.platform_of_point(start)
    platform_target = shared_map.platform_of_point(target)
    gap_h = platform_gap(platform_start, platform_target)

    if d_y == 0:
        if shared_map.is_continuous(start, target):
            return target
        elif platform_start and platform_target:
            tolerance = 4
            max_distance = DoubleJump.move_range.stop - tolerance * 2
            if gap_h in range(0, max_distance):
                if platform_start.end_x < platform_target.begin_x:
                    if platform_target.begin_x - start.x <= max_distance:
                        return target
                    return MapPoint(platform_start.end_x - int(tolerance / 2), platform_start.y, 3)
                else:
                    if start.x - platform_target.end_x <= max_distance:
                        return target
                    return MapPoint(platform_start.begin_x + int(tolerance / 2), platform_start.y, 3)
    elif d_y < 0:
        # 目标在上面， 优先向上移动
        tmp_y = MapPoint(start.x, target.y)
        if shared_map.is_continuous(tmp_y, target):
            if bot_status.player_moving:
                if bot_status.player_direction == 'left':
                    tmp_y = MapPoint(start.x - 3, target.y)
                else:
                    tmp_y = MapPoint(start.x + 3, target.y)
                if shared_map.is_continuous(tmp_y, target):
                    return MapPoint(start.x, target.y, 3)
                else:
                    time.sleep(0.5)
                    return find_next_point(bot_status.player_pos, target)
            else:
                return tmp_y
        tmp_x = MapPoint(target.x, start.y)
        if shared_map.is_continuous(start, tmp_x):
            if bot_status.player_moving:
                if bot_status.player_direction == 'left':
                    tmp = MapPoint(target.x - 3, target.y)
                else:
                    tmp = MapPoint(target.x + 3, target.y)
                if shared_map.is_continuous(tmp, target):
                    return MapPoint(target.x, start.y, 3)
                else:
                    time.sleep(0.5)
                    return find_next_point(bot_status.player_pos, target)
            else:
                return tmp_x
        if gap_h == -1 and platform_start and platform_target:
            x_start = list(range(platform_start.begin_x, platform_start.end_x))
            x_target = list(range(platform_target.begin_x, platform_target.end_x))
            x_intersection = list(set(x_start).union(set(x_target)))
            if len(x_intersection) > 0:
                x_intersection.sort()
                target_x = (x_intersection[0] + x_intersection[-1]) / 2
                return MapPoint(int(target_x), target.y, 3)
        elif gap_h > 0 and gap_h <= 8 and abs(d_y) <= 8 and platform_start and platform_target:
            if platform_start.end_x < platform_target.begin_x:
                return MapPoint(platform_start.end_x - 2, platform_start.y, 3)
            else:
                return MapPoint(platform_start.begin_x + 2, platform_start.y, 3)
        elif gap_h > 0:
            DoubleJump(target=target, attack_if_needed=True).execute()
            return find_next_point(bot_status.player_pos, target)
    else:
        # 目标在下面，优先向下移动
        tmp_y = MapPoint(start.x, target.y, 3)
        if shared_map.is_continuous(tmp_y, target):
            return tmp_y
        tmp_x = MapPoint(target.x, start.y, 3)
        if shared_map.is_continuous(tmp_x, start):
            return tmp_x
        if platform_start is not None and platform_target is not None and gap_h > 0 and gap_h <= DoubleJump.move_range.start:
            if platform_start.end_x < platform_target.begin_x:
                return MapPoint(platform_start.end_x - 2, platform_start.y, 3)
            else:
                return MapPoint(platform_start.begin_x + 2, platform_start.y, 3)
        elif gap_h > 0:
            DoubleJump(target=target, attack_if_needed=True).execute()
            return find_next_point(bot_status.player_pos, target)

    return shared_map.platform_point(MapPoint(target.x, target.y - 1, target.tolerance))

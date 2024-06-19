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

    # Buffs
    Transcendent_Cygnus_Blessing = '1'
    Glory_of_the_Guardians = '2'
    Shadow_Illusion = '3'
    LAST_RESORT = '4'
    Shadow_Spear = 'v'
    Shadow_Bat = 'f1'
    Dark_Elemental = 'f3'
    Darkness_Ascending = '6'

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
    Dominion = 'c'
    ERDA_SHOWER = '`'
    Phalanx_Charge = 'z'
    Greater_Dark_Servant = 'd'
    Shadow_Bite = 'e'
    Rapid_Throw = 'x'
    Silence = ''

    FOR_THE_GUILD = '8'
    HARD_HITTER = '7'

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
        DoubleJump(target=target, attack_if_needed=True).execute()
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
    elif abs(d_x) >= 22:
        DoubleJump(target=next_p, attack_if_needed=True).execute()
    elif shared_map.is_continuous(bot_status.player_pos, next_p):
        if abs(d_x) >= 11:
            Shadow_Dodge(direction).execute()
        else:
            Walk(target_x=next_p[0], tolerance=tolerance).execute()
    else:
        DoubleJump(target=next_p, attack_if_needed=True).execute()

#########################
#        Y轴移动         #
#########################


@bot_status.run_if_enabled
def move_up(target):
    p = bot_status.player_pos
    dy = abs(p[1] - target[1])

    if dy < 5:
        press(Keybindings.JUMP)
    elif dy <= 23:
        Jump_Up(target).execute()
    else:
        RopeLift(dy).execute()


@bot_status.run_if_enabled
def move_down(target):
    sleep_in_the_air(n=1)
    evade_rope()
    if target[1] > bot_status.player_pos[1]:
        Fall().execute()


class DoubleJump(Skill):
    """Performs a flash jump in the given direction."""
    key = Keybindings.Shadow_Jump
    type = SkillType.Move
    backswing = 0.1

    def __init__(self, target: tuple[int, int], attack_if_needed=False):
        super().__init__(locals())
        self.target = target
        self.attack_if_needed = attack_if_needed

    def main(self):
        while not self.canUse():
            print("double jump waiting")
            time.sleep(0.01)
        dx = self.target[0] - bot_status.player_pos[0]
        dy = self.target[1] - bot_status.player_pos[1]
        direction = 'left' if dx < 0 else 'right'
        start_y = bot_status.player_pos[1]

        self.__class__.castedTime = time.time()
        key_down(direction)
        time.sleep(0.1)
        press(Keybindings.JUMP, 1, down_time=0.03, up_time=0.03)
        press(Keybindings.JUMP, 1, down_time=0.02, up_time=0.03)
        if self.attack_if_needed:
            Quintuple_Star().execute()
        key_up(direction)
        # time.sleep(self.backswing)
        sleep_in_the_air(n=1)


# 上跳
class Jump_Up(Command):
    key = Keybindings.Shadow_Jump
    type = SkillType.Move

    def __init__(self, target):
        super().__init__(locals())
        self.target = target

    def main(self):
        sleep_in_the_air(n=4)
        press(opposite_direction(bot_status.player_direction))
        evade_rope(True)

        up_point = (bot_status.player_pos[0], self.target[1])
        if not shared_map.on_the_platform(up_point):
            move_horizontal((self.target[0], bot_status.player_pos[1]), 0)
        dy = bot_status.player_pos[1] - self.target[1]
        press(Keybindings.JUMP)
        key_down('up')
        time.sleep(0.06 if dy >= 20 else 0.1)
        press(Keybindings.JUMP, 1)
        key_up('up')
        sleep_in_the_air(n=10)

#########################
#        X轴移动         #
#########################


@bot_status.run_if_enabled
def move_horizontal(target, tolerance):
    if bot_status.player_pos[1] != target[1]:
        print("!!! move_horizontal error")
        return
    dx = target[0] - bot_status.player_pos[0]
    direction = 'left' if dx < 0 else 'right'
    while abs(dx) > tolerance:
        if abs(dx) >= 24:
            DoubleJump(target=target, attack_if_needed=True).execute()
        elif abs(dx) >= 10:
            Shadow_Dodge(direction).execute()
        else:
            Walk(target_x=target[0], tolerance=tolerance).execute()
        dx = target[0] - bot_status.player_pos[0]


class Shadow_Dodge(Skill):
    key = Keybindings.Shadow_Dodge
    type = SkillType.Move
    cooldown = 0
    precast = 0
    backswing = 0.5

    def __init__(self, direction='right'):
        super().__init__(locals())
        self.direction = bot_settings.validate_horizontal_arrows(direction)

    def main(self):
        if not self.canUse():
            return False

        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press(opposite_direction(self.direction))
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
    precast = 0.3
    backswing = 0.8
    duration = 55


class Replace_Dark_Servant(Skill):
    key = Keybindings.Greater_Dark_Servant
    type = SkillType.Move
    cooldown = 3
    backswing = 0.6


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


class Quintuple_Star(Skill):
    key = Keybindings.Quintuple_Star
    type = SkillType.Attack
    backswing = 0.5


class Dark_Omen(Skill):
    key = Keybindings.Dark_Omen
    type = SkillType.Attack
    cooldown = 20
    backswing = 0.9


class Shadow_Bite(Skill):
    key = Keybindings.Shadow_Bite
    type = SkillType.Attack
    cooldown = 15
    backswing = 0.55

    @classmethod
    def check(cls):
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.98)
        cls.ready = len(matchs) > 0


class Shadow_Spear(Skill):
    key = Keybindings.Shadow_Spear
    type = SkillType.Buff
    cooldown = 177
    backswing = 0.6


class Dominion(Skill):
    key = Keybindings.Dominion
    type = SkillType.Attack
    cooldown = 180
    ready = False

    def main(self):
        if not self.canUse():
            return False

        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, down_time=0.01, up_time=0.01)
        Shadow_Dodge().execute()
        return True

    @classmethod
    def check(cls):
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.95, debug=False)
        cls.ready = len(matchs) > 0


class Phalanx_Charge(Skill):
    key = Keybindings.Phalanx_Charge
    type = SkillType.Attack
    cooldown = 30
    backswing = 0.75
    
    @classmethod
    def check(cls):
        matchs = utils.multi_match(
            capture.skill_frame, cls.icon[2:-2, 12:-2], threshold=0.98)
        cls.ready = len(matchs) > 0


class Attack(Command):
    key = Quintuple_Star.key
    type = SkillType.Attack
    backswing = Quintuple_Star.backswing

    def main(self):
        Quintuple_Star().execute()


class Shadow_Attack(Command):
    @classmethod
    def canUse(cls, next_t: float = 0) -> bool:
        return True

    def main(self):
        # if Dominion.canUse():
        #     Dominion().execute()
        # el
        if Arachnid.canUse():
            Arachnid().execute()
            Dark_Omen().execute()
        elif Shadow_Bite.canUse():
            Shadow_Bite().execute()
        elif Dark_Omen.canUse():
            Dark_Omen().execute()
        else:
            Detect_Attack().execute()
        return True


class Detect_Attack(Command):
    def __init__(self, x=0, y=0):
        super().__init__(locals())
        self.x = int(x)
        self.y = int(y)

    def main(self):
        width = 300
        height = 100

        # if len(detect_mobs(
        #         capture.frame[self.y - height:self.y, self.x-width:self.x], MobType.NORMAL, multy_match=True)) > 0:
        #     press('left')
        # elif len(detect_mobs(
        #         capture.frame[self.y - height:self.y, self.x:self.x+width], MobType.NORMAL, multy_match=True)) > 0:
        #     press('right')
        # elif len(detect_mobs(
        #         capture.frame[height:height*2, width:width*2], MobType.NORMAL, multy_match=True)) > 0:
        #     press(Keybindings.JUMP)
        #     press('left')
        # elif len(detect_mobs(
        #         capture.frame[height:height*2, width*2:width*3], MobType.NORMAL, multy_match=True)) > 0:
        #     press(Keybindings.JUMP)
        #     press('right')
        Quintuple_Star().execute()
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

    def main(self):
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
                print(f"mobs count = {len(mobs)}")
                break
            if time.time() - start > 7:
                break
            if len(mobs) > 0:
                Detect_Attack(self.x, self.y).execute()

###################
#      Buffs      #
###################


class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            # Dark_Elemental,
            # Shadow_Bat,
            Transcendent_Cygnus_Blessing,
            LastResort,
            # Glory_of_the_Guardians,
            # Shadow_Spear,
            # Shadow_Illusion,
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


class LastResort(Skill):
    key = Keybindings.LAST_RESORT
    cooldown = 75
    precast = 0.3
    backswing = 0.8
    type = SkillType.Buff

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

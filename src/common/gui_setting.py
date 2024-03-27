from src.common.interfaces import Configurable


class AutoSettings(Configurable):
    DEFAULT_CONFIG = {
        'MVP': False,
        'Ask': False,
        'Mining': False,
        'Load Map': True,
        'Login': True,
        'Cube': False,
        'Channel': 33,
    }

    @property
    def mining(self):
        return self.get('Mining')

    @property
    def load_map(self):
        return self.get('Load Map')
    
    @property
    def auto_login(self):
        return self.get('Login')

    @property
    def cube(self):
        return self.get('Cube')
    
    @property
    def auto_login_channel(self):
        if self.auto_login:
            return self.get('Channel')
        else:
            return 0

class ModeSettings(Configurable):
    DEFAULT_CONFIG = {
        'type': 'mob'
    }
    
    @property
    def type(self):
        return self.get('type')
    
    @type.setter
    def type(self, value):
        self.set("type", value) 

class DetectSettings(Configurable):
    DEFAULT_CONFIG = {
        'Detect Mob': False,
        'Detect Elite': False,
        'Detect Boss': False
    }

    @property
    def detect_mob(self):
        return self.get('Detect Mob')

    @property
    def detect_elite(self):
        return self.get('Detect Elite')

    @property
    def detect_boss(self):
        return self.get('Detect Boss')


class BuffSettings(Configurable):
    DEFAULT_CONFIG = {
        'Guild Buff': False,
        'Guild Potion': False,
        'Exp Potion': False,
        'Wealthy Potion': False,
        'Gold Potion': False,
        'Candied Apple': False,
        'Legion Wealthy': False,
        'Exp Coupon': False
    }


class NotificationSettings(Configurable):
    DEFAULT_CONFIG = {
        'Telegram': True,
        'Wechat': False,
        'Email': False,
        'Game_Msg': False,
        'notice_level': 1
    }

    @property
    def notice_level(self):
        return self.get('notice_level')

    @property
    def telegram(self):
        return self.get('Telegram')

    @property
    def wechat(self):
        return self.get('Wechat')

    @property
    def game_msg(self):
        return self.get('Game_Msg')


class PetSettings(Configurable):
    DEFAULT_CONFIG = {
        'Auto-feed': False,
        'Num pets': 1
    }


class MiscSettings(Configurable):
    DEFAULT_CONFIG = {
        'Open Herb': False,
        'Open Mineral': False,
        'Cube': False,
        'Star': False,
    }


class ShadowerSettings(Configurable):
    DEFAULT_CONFIG = {
        'Meso Explosion': False,
        'Trickblade': False,
    }


class Gui_Setting():
    def __init__(self):
        self.mode = ModeSettings('mode')
        self.auto = AutoSettings('auto')
        self.detection = DetectSettings('detection')
        self.buff = BuffSettings('buff')
        self.notification = NotificationSettings('notification')
        self.pet = PetSettings('pet')
        self.misc = MiscSettings('misc')
        self.shadower = ShadowerSettings('shadower')


gui_setting = Gui_Setting()

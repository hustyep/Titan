from src.common.interfaces import Configurable

class AutoSettings(Configurable):
    DEFAULT_CONFIG = {
        'MVP': False,
        'Ask': False,
        'Mining': False,
        'Auto Load': True,
        'Detect Mob': False
    }
    
    @property
    def mining(self):
        return self.get('Mining')
    
    @property
    def auto_load(self):
        return self.get('Auto Load')
   
    @property
    def detect_mob(self):
        return self.get('Detect Mob') 
    
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
        'notice_level': 1
    }
    
    @property
    def notice_level(self):
        return self.get('notice_level')
    
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
        self.auto = AutoSettings('auto')
        self.buff = BuffSettings('buff')
        self.notification = NotificationSettings('notification')
        self.pet = PetSettings('pet')
        self.misc = MiscSettings('misc')
        self.shadower = ShadowerSettings('shadower')
        
gui_setting = Gui_Setting()

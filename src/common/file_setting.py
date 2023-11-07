from src.common.interfaces import Configurable

class File_Setting(Configurable):
    DEFAULT_CONFIG = {
        'command_book_path': 'resources/command_books/shadower.py',
        'routine_path': 'resources/routines/shadower/ResarchTrain1.csv'
    }
    
    @property
    def command_book_path(self):
        return self.config['command_book_path']
    
    @command_book_path.setter
    def command_book_path(self, value):
        self.config['command_book_path'] = value
    
    @property
    def routine_path(self):
        return self.config['routine_path']
    
    @routine_path.setter
    def routine_path(self, value):
        self.config['routine_path'] = value
import os
import inspect
import importlib
import traceback
from os.path import basename, splitext
from src.common import bot_settings, utils
from src.common.constants import CharacterType, RESOURCES_DIR
from src.command import commands

CB_KEYBINDING_DIR = os.path.join('resources', 'keybindings')

def get_command_book_path(character_name: str) -> str:
    target = os.path.join(RESOURCES_DIR,
                        'command_books', f'{character_name}.py')
    if not os.path.exists(target):
        raise ValueError(f"command book '{target}' is not exists.")
    return target

class CommandBook():
    def __init__(self, charactor: CharacterType):
        # importlib.reload(commands)
        self.charactor = charactor
        self.character_name = charactor.value

        file_path = get_command_book_path(self.character_name)
        result = self._load_commands(file_path)
        if result is None:
            raise ValueError(f"Invalid command book at '{file_path}'")
        self.dict, self.func_dict, self.module = result
        self.__update_default_commands()

        bot_settings.class_name = self.character_name

    def _load_commands(self, file):
        """Prompts the user to select a command module to import. Updates config's command book."""

        utils.print_separator()
        print(f"[~] Loading command book '{basename(file)}':")

        ext = splitext(file)[1]
        if ext != '.py':
            print(f" !  '{ext}' is not a supported file extension.")
            return

        # Import the desired command book file
        target = '.'.join(['resources', 'command_books', self.character_name])
        try:
            importlib.reload(commands)
            module = importlib.import_module(target)
            module = importlib.reload(module)
        except ImportError:     # Display errors in the target Command Book
            print(' !  Errors during compilation:\n')
            for line in traceback.format_exc().split('\n'):
                line = line.rstrip()
                if line:
                    print(' ' * 4 + line)
            print(f"\n !  Command book '{self.character_name}' was not loaded")
            return

        new_func = {}
        new_cb = {}
        # load default Fuction
        for name, func in inspect.getmembers(commands, inspect.isfunction):
            module_name = inspect.getmodule(inspect.unwrap(func)).__name__
            if module_name == commands.__name__:
                new_func[name] = func

        # load default Command
        for name, command in inspect.getmembers(commands, inspect.isclass):
            if inspect.getmodule(command).__name__ == commands.__name__:
                new_cb[name] = command

        # Populate the new command book
        for name, func in inspect.getmembers(module, inspect.isfunction):
            module_name = inspect.getmodule(inspect.unwrap(func)).__name__
            if module_name == module.__name__:
                new_func[name] = func

        for name, command in inspect.getmembers(module, inspect.isclass):
            if inspect.getmodule(command).__name__ == module.__name__:
                new_cb[name] = command

        # Check if required functions have been implemented and overridden
        required_function_found = True
        for func_name in ['step']:
            func = new_func[func_name]
            module_name = inspect.getmodule(inspect.unwrap(func)).__name__
            if module_name == commands.__name__:
                required_function_found = False
                raise ValueError(
                    f" !  Error: Must implement required function '{func_name}'.")

        # Check if required commands have been implemented and overridden
        required_command_found = True
        for name, cls in new_cb.items():
            if inspect.isabstract(cls):
                required_command_found = False
                raise ValueError(
                    f" !  Error: Must implement required command '{name}'.")

        if required_command_found and required_function_found:
            print(f" ~  Successfully loaded command book '{self.character_name}'")
            return new_cb, new_func, module
        else:
            print(f" !  Command book '{self.character_name}' was not loaded")

    def __update_default_commands(self):
        # replace function
        for func_name, func in self.func_dict.items():
            if hasattr(commands, func_name):
                setattr(commands, func_name, func)

        # replace class
        for class_name, cls in self.dict.items():
            if hasattr(commands, class_name):
                setattr(commands, class_name, cls)

        # pre load
        for skill in self.dict.values():
            if issubclass(skill, commands.Skill):
                skill.load()

    def reset(self):
        for name, command in inspect.getmembers(self.module, inspect.isclass):
            if issubclass(command, commands.Command):
                command.castedTime = 0

    def __getitem__(self, item):
        return self.dict[item]

    def __contains__(self, item):
        return item in self.dict

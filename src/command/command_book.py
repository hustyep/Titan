import os
import inspect
import importlib
import traceback
from os.path import basename, splitext
from src.common import bot_settings, utils
from src.command import commands

CB_KEYBINDING_DIR = os.path.join('resources', 'keybindings')


class CommandBook():
    def __init__(self, file):
        # importlib.reload(commands)
        self.name = splitext(basename(file))[0]

        result = self._load_commands(file)
        if result is None:
            raise ValueError(f"Invalid command book at '{file}'")
        self.dict, self.func_dict, self.module = result
        self.__load_default_commands()

        bot_settings.class_name = self.name

    def _load_commands(self, file):
        """Prompts the user to select a command module to import. Updates config's command book."""

        utils.print_separator()
        print(f"[~] Loading command book '{basename(file)}':")

        ext = splitext(file)[1]
        if ext != '.py':
            print(f" !  '{ext}' is not a supported file extension.")
            return

        # Import the desired command book file
        target = '.'.join(['resources', 'command_books', self.name])
        try:
            module = importlib.import_module(target)
            module = importlib.reload(module)
            importlib.reload(commands)
        except ImportError:     # Display errors in the target Command Book
            print(' !  Errors during compilation:\n')
            for line in traceback.format_exc().split('\n'):
                line = line.rstrip()
                if line:
                    print(' ' * 4 + line)
            print(f"\n !  Command book '{self.name}' was not loaded")
            return

        new_func = {}
        new_cb = {}
        # load default Fuction
        for name, func in inspect.getmembers(commands, inspect.isfunction):
            new_func[name.lower()] = func

        # load default Command
        for name, command in inspect.getmembers(commands, inspect.isclass):
            if issubclass(command, commands.Command):
                new_cb[name.lower()] = command

        # Populate the new command book
        for name, func in inspect.getmembers(module, inspect.isfunction):
            new_func[name.lower()] = func

        for name, command in inspect.getmembers(module, inspect.isclass):
            if issubclass(command, commands.Command):
                new_cb[name.lower()] = command

        # Load key map
        if hasattr(module, 'Keybindings'):
            commands.Keybindings = module.Keybindings
        else:
            print(
                f" !  Error loading command book '{self.name}', keymap class 'Keybindings' is missing")
            return

        # Check if required functions have been implemented and overridden
        required_function_found = True
        for func_name in ['step']:
            if func_name not in new_func:
                required_function_found = False
                raise ValueError(
                    f" !  Error: Must implement required function '{func_name}'.")

        # Check if required commands have been implemented and overridden
        required_command_found = True
        for command in [commands.Buff, commands.Attack, commands.DoubleJump]:
            name = command.__name__.lower()
            if name not in new_cb:
                required_command_found = False
                new_cb[name] = command
                raise ValueError(
                    f" !  Error: Must implement required command '{name}'.")

        if required_command_found and required_function_found:
            print(f" ~  Successfully loaded command book '{self.name}'")
            return new_cb, new_func, module
        else:
            print(f" !  Command book '{self.name}' was not loaded")
            
    
    def __load_default_commands(self):
        commands.step = self.func_dict['step']
        commands.Attack = self.dict["attack"]
        commands.DoubleJump = self.dict["doublejump"]

        if self.dict["summon"]:
            commands.Summon = self.dict["summon"]
        else:
            commands.Summon = commands.Skill
        if self.dict["dotaoe"]:
            commands.DotAoe = self.dict["dotaoe"]
        else:
            commands.DotAoe = commands.Skill
        if self.dict["aoe"]:
            commands.Aoe = self.dict["aoe"]
        else:
            commands.Aoe = commands.Skill
        if self.dict["buff"]:
            commands.Buff = self.dict["buff"]

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

from src.common.constants import *
from src.command.command_book import CommandBook
from src.command import commands


class CharacterModel:
    def __init__(self, charactorType: CharacterType):
        self.charactor_type = charactorType

        info = Charactor_Map[charactorType]
        self.branch: CharacterBranchType = info["branch"]
        self.group: CharacterBranchType = info["group"]
        self.main_stat: MainStatType = info["main_stat"]
        self.command_book = CommandBook(charactorType)

    def update_skill_status(self):
        for skill in self.command_book.dict.values():
            if issubclass(skill, commands.Skill) and skill.key is not None and skill.cooldown > 0:
                skill.check()


Charactor_Map = {
    CharacterType.Shadower: {
        "branch": CharacterBranchType.Thief,
        "group": CharacterGroupType.Explorer,
        "main_stat": MainStatType.LUK},
    CharacterType.NightLord: {
        "branch": CharacterBranchType.Thief,
        "group": CharacterGroupType.Explorer,
        "main_stat": MainStatType.LUK},
    CharacterType.Hero: {
        "branch": CharacterBranchType.Warrior,
        "group": CharacterGroupType.Explorer,
        "main_stat": MainStatType.STR},
    CharacterType.NightWalker: {
        "branch": CharacterBranchType.Thief,
        "group": CharacterGroupType.Cygnus,
        "main_stat": MainStatType.LUK},
}

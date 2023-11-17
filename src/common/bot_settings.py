import cv2
import os
from src.common.constants import RESOURCES_DIR
from src.common.file_setting import File_Setting

"""p
A list of user-defined settings that can be changed by routines. Also contains a collection
of validator functions that can be used to enforce parameter types.
"""


#################################
#      Validator Functions      #
#################################
def validate_nonnegative_int(value):
    """
    Checks whether VALUE can be a valid non-negative integer.
    :param value:   The string to check.
    :return:        VALUE as an integer.
    """

    if int(value) >= 0:
        return int(value)
    raise ValueError(f"'{value}' is not a valid non-negative integer.")


def validate_nonnegative_float(value):
    """
    Checks whether VALUE can be a valid non-negative integer.
    :param value:   The string to check.
    :return:        VALUE as an integer.
    """

    if float(value) >= 0:
        return float(value)
    raise ValueError(f"'{value}' is not a valid non-negative float.")


def validate_boolean(value):
    """
    Checks whether VALUE is a valid Python boolean.
    :param value:   The string to check.
    :return:        VALUE as a boolean
    """

    value = value.lower()
    if value in {'true', 'false'}:
        return True if value == 'true' else False
    elif int(value) in {0, 1}:
        return bool(int(value))
    raise ValueError(f"'{value}' is not a valid boolean.")


def validate_arrows(key):
    """
    Checks whether string KEY is an arrow key.
    :param key:     The key to check.
    :return:        KEY in lowercase if it is a valid arrow key.
    """

    if isinstance(key, str):
        key = key.lower()
        if key in ['up', 'down', 'left', 'right']:
            return key
    raise ValueError(f"'{key}' is not a valid arrow key.")


def validate_horizontal_arrows(key):
    """
    Checks whether string KEY is either a left or right arrow key.
    :param key:     The key to check.
    :return:        KEY in lowercase if it is a valid horizontal arrow key.
    """

    if isinstance(key, str):
        key = key.lower()
        if key in ['left', 'right']:
            return key
    raise ValueError(f"'{key}' is not a valid horizontal arrow key.")


#########################
#       Settings        #
#########################
# A dictionary that maps each setting to its validator function
SETTING_VALIDATORS = {
    'move_tolerance': int,
    'adjust_tolerance': int,
    'record_layout': validate_boolean,
    'mini_margin': int,
}


def reset():
    """Resets all settings to their default values."""

    global move_tolerance, adjust_tolerance, record_layout, mini_margin
    global role_name, class_name, role_template, boundary_point_l, boundary_point_r

    move_tolerance = 13
    adjust_tolerance = 3
    record_layout = False
    mini_margin = 0

    role_name = ''
    class_name = ''
    role_template = None
    boundary_point_l = (100, 0)
    boundary_point_r = (0, 0)


def load_role_template():
    global role_template

    if len(role_name) > 0:
        try:
            role_template = cv2.imread(
                f'assets/roles/player_{role_name}_template.png', 0)
        except:
            raise ValueError(f"role template '{role_template}' is not exists.")


def get_command_book_path(command_name=None):
    if command_name is None:
        command_name = class_name
    target = os.path.join(RESOURCES_DIR,
                          'command_books', f'{command_name}.py')
    if not os.path.exists(target):
        print(f"command book '{target}' is not exists.")
        # raise ValueError(f"command book '{target}' is not exists.")
    return target


def get_routines_dir(command_name=None):
    if command_name is None:
        command_name = class_name
    target = os.path.join(RESOURCES_DIR,
                          'routines', command_name)
    if not os.path.exists(target):
        os.makedirs(target)
    return target


# The allowed error from the destination when moving towards a Point
move_tolerance = 13

# The allowed error from a specific location while adjusting to that location
adjust_tolerance = 3

# Whether the bot should save new player positions to the current layout
record_layout = False

mini_margin = 0

class_name = ''

# The name of the role
role_name = ''

role_template = None

boundary_point_l = (100, 0)
boundary_point_r = (0, 0)

file_setting: File_Setting = None

################################
#       Notifier Config        #
################################

wechat_name = 'yep'

# 填写真实的发邮件服务器用户名、密码
mail_user = 'mars_maple@163.com'
mail_password = 'KQJKXCWSVPGOWPEW'
# 实际发给的收件人
mail_to_addrs = '326143583@qq.com'

telegram_apiToken = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
# telegram_apiToken = '6497654972:AAExWRJvmuswPb2MzbtHi8fIp140TdeDSQM'

telegram_chat_id = '805381440'

reset()

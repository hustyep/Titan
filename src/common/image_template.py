import cv2
from src.common.dll_helper import dll_helper
from src.common import utils

ASSETS_PATH = 'assets/'

###########################
#      common ranges      #
###########################

GREEN_RANGES = (
    ((50, 200, 46), (77, 255, 255)),
)
RED_RANGES = (
    ((0, 43, 46), (10, 255, 255)),
    ((156, 43, 46), (180, 255, 255)),
)
YELLOW_RANGES = (
    ((26, 43, 46), (34, 255, 255)),
)
BLUE_RANGES = (
    ((100, 43, 46), (124, 255, 255)),
)
ORANGE_RANGES = (
    ((11, 43, 46), (25, 255, 255)),
)
WHITE_RANGES = (
    ((0, 0, 150), (180, 30, 255)),
)
GRAY_RANGES = (
    ((0, 0, 46), (180, 43, 255)),
)
BLACK_RANGES = (
    ((0, 0, 0), (180, 255, 46)),
)
TEXT_WHITE_RANGES = (
    ((0, 0, 150), (180, 30, 255)),
    ((0, 0, 46), (180, 43, 255)),
)

# https://blog.csdn.net/weixin_45946270/article/details/124827045

# The rune's buff
RUNE_BUFF_TEMPLATE = cv2.imread(f'{ASSETS_PATH}rune/rune_buff_template.png', 0)
RUNE_BUFF_GRAY_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}rune/rune_buff_gray_template.png', 0)

######################
#     system UI      #
######################
BUTTON_CONFIRM_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/btn_confirm_template.png', 0)
BUTTON_OK_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/btn_ok_template.png', 0)
BUTTON_CANCEL_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/btn_cancel_template.png', 0)
BUTTON_ERROR_OK_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/disconnect_ok_template.png', 0)
BUTTON_CHANGE_REGION_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/change_region_template.png', 0)
END_TALK_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/end_talk_template.png', 0)
END_PLAY_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/btn_play_template.png', 0)
GUIDE_PLUSE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/btn_guide_plus_template.png', 0)
MAPLE_REWARD_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/maple_reward_template.png', 0)
ADV_CLOSE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/adv_close_template.png', 0)
SUNNY_SUNDAY_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/sunny_sunday_template.png', 0)
CHAT_MINI_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/chat_mini_template.png', 0)
Go_Ardentmill_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/GoArdentmill.png', 0)
SETTING_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/setting_template.png', 0)
QUEST_BUBBLE_TEMPLATE = utils.filter_color(cv2.imread(
    f'{ASSETS_PATH}common/quest_bubble.png'), YELLOW_RANGES)
ITEM_CASH_TAB_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}common/item_cash_tab.png', 0)
ITEM_CASH_TAB_HIGHLIGHT_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}common/item_cash_tab_highlight.png', 0)
TELEPORT_STONE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}common/teleport_stone.png', 0)
TELEPORT_STONE_MOVE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}teleport/telepot_move.png', 0)
TELEPORT_STONE_SCROLL_DOWN_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}teleport/list_scroll_down.png', 0)
TELEPORT_STONE_CLOSE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}teleport/teleport_close.png', 0)
TELEPORT_STONE_SHOW_TOWNS_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}teleport/show_towns.png', 0)
TELEPORT_STONE_LIST_ICON_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}teleport/teleport_stone_list_icon.png', 0)
INVENTORY_MESO_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/meso_icon_template.png', 0)
TELEPORT_CURRENT_MAP_ERROR_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}teleport/same_map.png', 0)

########################
#      exceptions      #
########################
GM_HAT_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/GM_Hat.webp', 0)
GM_HAT_W_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/gm_hat_w.png', 0)
# dead alert
DEAD_TOBBSTONE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/dead_tombstone_template.png', 0)
DEAD_OK_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/dead_ok_template.png', 0)

SKULL_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/skull_template.png', 0)

# tabbar icon
TABBAR_MAPLE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/icon_maplestory_template.png', 0)
TABBAR_WECHAT_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/icon_wechat_template.png', 0)
TABBAR_NX_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/icon_nx_launcher_template.png', 0)

# The Elite Boss's warning sign
ELITE_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/elite_template.jpg', 0)
BOSS_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/boss_template.png', 0)

# White Room
WHITE_ROOM_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/white_room_template.png', 0)

WECHAT_CALL_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}exceptions/wechat_call.png', 0)
WECHAT_CALL_TEMPLATE_2X = cv2.imread(
    f'{ASSETS_PATH}exceptions/wechat_call@2x.png', 0)

# cube
POTENTIAL_ATT13_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/att13.png', 0)
POTENTIAL_ATT10_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/att10.png', 0)
POTENTIAL_ATT12_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/att12.png', 0)
POTENTIAL_ATT9_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/att9.png', 0)
POTENTIAL_RESULT_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/cube_result.png', 0)
POTENTIAL_AFTER_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/cube_after.png', 0)
POTENTIAL_LEGENDARY_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/legendary.png', 0)
POTENTIAL_LUK13_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/luk13.png', 0)
POTENTIAL_LUK12_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/luk12.png', 0)
POTENTIAL_LUK10_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/luk10.png', 0)
POTENTIAL_LUK9_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/luk9.png', 0)
POTENTIAL_STR13_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/str13.png', 0)
POTENTIAL_STR12_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/str12.png', 0)
POTENTIAL_STR10_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/str10.png', 0)
POTENTIAL_STR9_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/str9.png', 0)
POTENTIAL_ALL10_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/all10.png', 0)
POTENTIAL_ALL9_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/all9.png', 0)
POTENTIAL_ALL7_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/all7.png', 0)
POTENTIAL_ALL6_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/all6.png', 0)
POTENTIAL_MESOS_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/mesos.png', 0)
POTENTIAL_DROP_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/drop.png', 0)
POTENTIAL_CD8_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/critical_damage.png', 0)
POTENTIAL_CD2_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/cd2.png', 0)
POTENTIAL_CD1_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/cd1.png', 0)
POTENTIAL_BOSS40_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/boss40.png', 0)
POTENTIAL_BOSS3x_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/boss3x.png', 0)
POTENTIAL_DEF_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/def.png', 0)
ATT_INCREASE_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/att_increase.png', 0)
LUK_PLUS_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/luck_plus.png', 0)
ATT_PLUS_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/att_plus.png', 0)
ALL_PLUS_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}potential/all_stats_plus.png', 0)

#####################
#      mineral      #
#####################

MINAL_HEART_TEMPLATE = cv2.imread(
    'assets/mineral/mineral_heart_template.png', 0)
HERB_YELLOW_TEMPLATE = cv2.imread('assets/mineral/herb_yellow_template.png', 0)
HERB_PURPLE_TEMPLATE = cv2.imread('assets/mineral/herb_purple_template.png', 0)
MINAL_CRYSTAL_TEMPLATE = cv2.imread(
    'assets/mineral/mineral_crystal_template.png', 0)

####################
#     minimap      #
####################

# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(
    cv2.imread(f'{ASSETS_PATH}minimap/minimap_rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY)  # type: ignore

# Other players' symbols on the minimap
OTHER_RANGES = (
    ((0, 245, 215), (10, 255, 255)),
)
other_filtered = utils.filter_color(cv2.imread(
    f'{ASSETS_PATH}minimap/minimap_other_template.png'), OTHER_RANGES)
OTHER_TEMPLATE = cv2.cvtColor(other_filtered, cv2.COLOR_BGR2GRAY)

# guildmate' symbols on the minimap
GUILDMATE_RANGES = (
    ((120, 40, 180), (120, 110, 255)),
)
guildmate_filtered = utils.filter_color(cv2.imread(
    f'{ASSETS_PATH}minimap/minimap_guildmate_template.png'), GUILDMATE_RANGES)
GUILDMATE_TEMPLATE = cv2.cvtColor(guildmate_filtered, cv2.COLOR_BGR2GRAY)

# Offset in pixels to adjust for windowed mode
WINDOWED_OFFSET_TOP = 36
WINDOWED_OFFSET_LEFT = 10

# The top-left and bottom-right corners of the minimap
MM_TL_BMP = dll_helper.loadImage(f'{ASSETS_PATH}minimap/minimap_border_tl.bmp')
MM_BR_BMP = dll_helper.loadImage(f'{ASSETS_PATH}minimap/minimap_border_br.bmp')
MM_ME_BMP = dll_helper.loadImage(f'{ASSETS_PATH}minimap/minimap_me.bmp')

# The player's symbol on the minimap
PLAYER_TEMPLATE = cv2.imread(
    f'{ASSETS_PATH}minimap/minimap_player_template.png', 0)
PLAYER_TEMPLATE_L = cv2.imread(
    f'{ASSETS_PATH}minimap/minimap_player_template_l.png', 0)
PLAYER_TEMPLATE_R = cv2.imread(
    f'{ASSETS_PATH}minimap/minimap_player_template_r.png', 0)

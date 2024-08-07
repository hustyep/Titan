import threading
import time
import datetime
from enum import Enum
import numpy as np
import cv2
import pytesseract as tess
from src.common.gui_setting import gui_setting
from src.common import bot_status

if __name__ != "__main__":
    from src.modules.capture import capture
    from src.modules.notifier import notifier
    from src.chat_bot.chat_bot import chat_bot
    from src.common.gui_setting import gui_setting
    from src.common.constants import *
    from src.common import utils


SYSTEM_MSG_RANGES = (
    ((0, 0, 150), (180, 30, 255)),
    ((0, 0, 221), (180, 43, 255)),
    ((0, 0, 0), (180, 255, 30)),
)
WORLD_MSG_RANGES = (
    ((30, 200, 100), (80, 255, 255)),
)
WHITE_RANGES = (
    # ((0, 0, 100), (180, 50, 255)),
    ((0, 0, 150), (180, 43, 255)),
)
MAX_MSG_HEIGHT = 100


def filter_color(img, ranges):
    """
    Returns a filtered copy of IMG that only contains pixels within the given RANGES.
    on the HSV scale.
    :param img:     The image to filter.
    :param ranges:  A list of tuples, each of which is a pair upper and lower HSV bounds.
    :return:        A filtered copy of IMG.
    """
    if img is None or img.size == 0:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, ranges[0][0], ranges[0][1])
    for i in range(1, len(ranges)):
        mask = cv2.bitwise_or(mask, cv2.inRange(
            hsv, ranges[i][0], ranges[i][1]))

    # Mask the image
    color_mask = mask > 0
    result = np.zeros_like(img, np.uint8)
    result[color_mask] = img[color_mask]
    return result


class GameMsgType(Enum):
    NORMAL = '[normal msg]'
    GM = '[GM msg]'


class GameMsg:

    def __init__(self, text: str, type: GameMsgType, image) -> None:
        self.type = type
        self.text = text
        self.image = image
        self.timestamp = time.time()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, GameMsg):
            if self.type != __value.type:
                return False
            ratio = utils.string_similar(self.text, __value.text)
            return ratio >= 0.8
        return False

    def __str__(self):
        variables = self.__dict__
        result = self.type.value
        if len(variables) - 1 > 0:
            result += ':'
        for key, value in variables.items():
            if key != 'image' and key != 'type':
                result += f'\n  {key} = {value}'
        return result


class MsgCapture:

    def __init__(self):
        super().__init__()

        self.msg_list = []
        self.last_nomarl_msg = None

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Chat Capture's thread."""

        print('\n[~] Started chat capture')
        self.thread.start()

    @property
    def last_msg(self):
        if not self.msg_list:
            return
        return self.msg_list[-1]

    def _main(self):
        self.ready = True

        while True:
            if gui_setting.notification.game_msg and capture.msg_frame is not None and len(capture.msg_frame) > 0:
                new_msg = self.get_new_msg(capture.msg_frame)
                if new_msg and new_msg != self.last_msg:
                    self.msg_list.append(new_msg)
                    self.notify_new_msg(new_msg)
            time.sleep(0.5)

    def get_new_msg(self, frame) -> GameMsg | None:
        msg_list = self.image_to_str(frame, WHITE_RANGES)

        if len(msg_list) == 0:
            return None
        new_msg = msg_list.pop()
        if bot_status.white_room:
            return GameMsg(new_msg, GameMsgType.GM, image)
        else:
            return GameMsg(new_msg, GameMsgType.NORMAL, image)

    def notify_new_msg(self, msg: GameMsg):
        text = f'{"📢" if msg.type == GameMsgType.GM else "💬"}{msg.text}'
        print(text)
        # if (BotFatal.WHITE_ROOM in notifier.notice_time_record and notifier.notice_time_record[BotFatal.WHITE_ROOM] > 0) or gui_setting.notification.notice_level >= 4:
        path = 'screenshot/msgs'
        image_path = utils.save_screenshot(
            frame=msg.image, file_path=path, compress=False)
        chat_bot.send_message(text=text, image_path=image_path)

    def image_to_str(self, image, ranges=None):
        if ranges:
            image = filter_color(image, ranges)
        # cv2.imshow("", image)
        # cv2.waitKey(0)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        text = tess.image_to_string(image_rgb, lang="eng")
        content = text.replace("\f", "").split("\n")

        list = []
        for item in content:
            if len(item.strip()) == 0:
                continue
            if item.startswith('[') and len(item) > 6 and item[6] == ']':
                list.append(item)
            elif len(list) > 0:
                new = list.pop() + item
                list.append(new)

        return list


msg_capture = MsgCapture()


if __name__ == "__main__":
    image = cv2.imread(".test/3.png")
    # image = image[-64:-29, 2:400]
    # image = image[-500:-439, 2:400]
    # text = chat_capture.image_to_str(image)
    msg = msg_capture.get_new_msg(image, GameMsgType.SYSTEM)
    print(str(msg))
    # while True:
    #     new_msg = chat_capture.get_new_msg(image, GameMsgType.MVP)
    #     if new_msg and not new_msg.equal(msg):
    #         print("New Msg")
    #     time.sleep(0.5)

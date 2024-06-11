"""A collection of functions and classes used across multiple modules."""

# import aircv as ac
import time
import math
import queue
import os
import threading
import string
from datetime import datetime, timedelta
from random import random
import win32gui
import win32ui
import win32con
import cv2
import numpy as np
from PIL import Image, ImageDraw
import pytesseract as tess
import difflib
from python_calamine import CalamineWorkbook

def single_match(frame, template):
    """
    Finds the best match within FRAME.
    :param frame:       The image in which to search for TEMPLATE.
    :param template:    The template to match with.
    :return:            The top-left and bottom-right positions of the best match.
    """

    if frame is None or template is None:
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if (template.ndim > 2):
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, _, _, top_left = cv2.minMaxLoc(result)
    if top_left is not None:
        h, w = template.shape[::-1]
        bottom_right = (top_left[0] + w, top_left[1] + h)
        return top_left, bottom_right


def multi_match(frame, template, threshold=0.95, center=True, debug=False):
    """
    Finds all matches in FRAME that are similar to TEMPLATE by at least THRESHOLD.
    :param frame:       The image in which to search.
    :param template:    The template to match with.
    :param threshold:   The minimum percentage of TEMPLATE that each result must match.
    :return:            An array of matches that exceed THRESHOLD.
    """

    if frame is None or template is None or template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if (template.ndim > 2):
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))
    results = []
    src_copy = frame.copy()
    for p in locations:
        if center:
            x = int(round(p[0] + template.shape[1] / 2))
            y = int(round(p[1] + template.shape[0] / 2))
        else:
            x, y = p
        results.append((x, y))

        cv2.rectangle(src_copy, p, (p[0]+template.shape[1],
                      p[1]+template.shape[0]), (0, 0, 225), 2)
    if debug:
        cv2.imshow("result", src_copy)
        cv2.waitKey()
    return results


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


def add_mask(img, pos, **kwargs):
    transp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(transp, "RGBA")
    draw.rectangle(pos, **kwargs)
    new_img = Image.alpha_composite(img, transp).convert('RGB')
    open_cv_image = np.array(new_img)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


def trans_point(point: tuple[int, int], ratio: float):
    return int(point[0] * ratio), int(point[1] * ratio)


def draw_location(minimap, pos: tuple[int, int], ratio: float, color, tolerance):
    """
    Draws a visual representation of POINT onto MINIMAP. The radius of the circle represents
    the allowed error when moving towards POINT.
    :param minimap:     The image on which to draw.
    :param pos:         The location (as a tuple) to depict.
    :param color:       The color of the circle.
    :return:            None
    """

    # center = convert_to_absolute(pos, minimap)
    cv2.circle(minimap,
               trans_point(pos, ratio),
               round(tolerance * ratio),
               color,
               1)


def distance(a, b):
    """
    Applies the distance formula to two points.
    :param a:   The first point.
    :param b:   The second point.
    :return:    The distance between the two points.
    """

    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def separate_args(arguments):
    """
    Separates a given array ARGUMENTS into an array of normal arguments and a
    dictionary of keyword arguments.
    :param arguments:    The array of arguments to separate.
    :return:             An array of normal arguments and a dictionary of keyword arguments.
    """

    args = []
    kwargs = {}
    for a in arguments:
        a = a.strip()
        index = a.find('=')
        if index > -1:
            key = a[:index].strip()
            value = a[index+1:].strip()
            kwargs[key] = value
        else:
            args.append(a)
    return args, kwargs


def bernoulli(p):
    """
    Returns the value of a Bernoulli random variable with probability P.
    :param p:   The random variable's probability of being True.
    :return:    True or False.
    """

    return random() < p


def print_separator():
    """Prints a 3 blank lines for visual clarity."""

    print('\n')


def print_tag(tag):
    print_separator()
    print('#' * (10 + len(tag)))
    print(f"#    {tag}    #")
    print('#' * (10 + len(tag)))


def print_state(enabled):
    """Prints whether Mars is currently enabled or disabled."""
    print_tag('ENABLED ' if enabled else 'DISABLED')

##########################
#       Threading        #
##########################


class Async(threading.Thread):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.queue = queue.Queue()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.function(*self.args, **self.kwargs)
        self.queue.put('x')

    def process_queue(self, root):
        def f():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                root.after(100, self.process_queue(root))
        return f


def async_callback(context, function, *args, **kwargs):
    """Returns a callback function that can be run asynchronously by the GUI."""

    def f():
        task = Async(function, *args, **kwargs)
        task.start()
        context.after(100, task.process_queue(context))
    return f


def timeStr() -> str:
    now = datetime.utcnow() + timedelta(hours=8)
    return now.strftime('%y%m%d%H%M%S%f')[:-3]
    # return time.strftime("%y%m%d%H%M%S%f", time.localtime())[:-3]


def make_dir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)


def save_screenshot(frame, file_path=None, compress=True):
    if frame is None:
        return None

    if file_path is None:
        file_path = 'screenshot/tmp'

    make_dir(file_path)

    filename = f'{file_path}/maple_{timeStr()}'
    if compress:
        threading.Timer(1, cv2.imwrite, (filename + '.png', frame)).start()
        cv2.imwrite(filename + '.webp', frame,
                    [int(cv2.IMWRITE_WEBP_QUALITY), 0])
        return filename + '.webp'
    else:
        cv2.imwrite(filename + ".png", frame)
        return filename + ".png"

#########################
#        Capture        #
#########################

# 通过窗口句柄截取当前句柄图片 返回cv2格式的Mat数据


def window_capture(hwnd, picture_name=None):
    if not hwnd:
        return None

    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小
    hwndDC = win32gui.GetWindowDC(hwnd)  # 通过应用窗口句柄获得窗口DC
    # 通过hwndDC获得mfcDC(注意主窗口用的是win32gui库，操作位图截图是用win32ui库)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    # 创建兼容DC，实际在内存开辟空间（ 将位图BitBlt至屏幕缓冲区（内存），而不是将屏幕缓冲区替换成自己的位图。同时解决绘图闪烁等问题）
    cacheDC = mfcDC.CreateCompatibleDC()
    savebitmap = win32ui.CreateBitmap()  # 创建位图
    width = x2 - x1
    height = y2 - y1
    try:
        savebitmap.CreateCompatibleBitmap(mfcDC, width, height)  # 设置位图的大小以及内容
    except Exception as e:
        print(e)
        return None
    cacheDC.SelectObject(savebitmap)  # 将位图放置在兼容DC，即 将位图数据放置在刚开辟的内存里
    cacheDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0),
                   win32con.SRCCOPY)  # 截取位图部分，并将截图保存在剪贴板
    if picture_name is not None:
        # 将截图数据从剪贴板中取出，并保存为bmp图片
        savebitmap.SaveBitmapFile(cacheDC, picture_name)
    img_buf = savebitmap.GetBitmapBits(True)

    img = np.frombuffer(img_buf, dtype="uint8")
    img.shape = (height, width, 4)
    # mat_img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)  # 转换RGB顺序

    # cv2.imshow('MapleStory', img)
    # cv2.waitKey()

    # 释放内存
    win32gui.DeleteObject(savebitmap.GetHandle())
    cacheDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    return img


def maple_screenshot():
    hwnd = win32gui.FindWindow(None, "MapleStory")
    if hwnd != 0:
        img_name = f"maple_{int(time.time() * 1000)}.png"
        img = window_capture(hwnd, img_name)
        return img


def image_2_str(image) -> str:
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    text = tess.image_to_string(image_rgb, lang="eng")
    content = text.replace("\f", "")
    return content


def image_match_text(frame, list: list[str], threshold=0.7, filter=[' ']):
    text = image_2_str(frame).replace('\n', '').lower()
    for c in filter:
        text.replace(c, '')
    for i in string.punctuation:
        if i not in ['-', "'"]:
            text = text.replace(i, '')
    best = 0
    result: str = None
    for value in list:
        ratio = string_similar(text, value.lower())
        if ratio == 1:
            return value
        elif ratio > best:
            best = ratio
            result = value
    if best >= threshold:
        return result


def show_image(image, title=''):
    cv2.imshow(title, image)
    cv2.waitKey()


def string_similar(s1, s2):
    seq = difflib.SequenceMatcher(None, s1, s2)
    ratio = seq.ratio()
    return ratio


def cvt2Plt(cv_image):
    rgb_img = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb_img)
    return image

def iter_excel_calamine(file: str):
    workbook = CalamineWorkbook.from_path(file)
    rows = iter(workbook.get_sheet_by_index(0).to_python())
    headers = list(map(str, next(rows)))
    for row in rows:
        yield dict(zip(headers, row))
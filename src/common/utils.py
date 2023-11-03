"""A collection of functions and classes used across multiple modules."""

# import aircv as ac
import time
import math
import queue
import os
import threading
from datetime import datetime, timedelta
from random import random

import cv2
import numpy as np


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


def multi_match(frame, template, threshold=0.95, debug=False):
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
        x = int(round(p[0] + template.shape[1] / 2))
        y = int(round(p[1] + template.shape[0] / 2))
        results.append((x, y))

        cv2.rectangle(src_copy, p, (p[0]+template.shape[1],
                      p[1]+template.shape[0]), (0, 0, 225), 2)
    if debug:
        cv2.imshow("result", src_copy)
        cv2.waitKey()
    return results

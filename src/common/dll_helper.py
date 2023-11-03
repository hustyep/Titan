import ctypes
from ctypes import *
from ctypes import wintypes
import time
from src.common.hid import hid
import threading

class DllHelper:
    
    def __init__(self):
        self.dll = cdll.LoadLibrary('./MarsDLL.dll')
        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True
        
        self.ImageSearch = self.dll.ImageSearch
        self.ImageSearch.restype = ctypes.c_char_p
        self.ImageSearch.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_char_p,wintypes.HBITMAP,wintypes.HBITMAP]

    def start(self):
        print('\n[~] Started load dll')
        self.thread.start()

    def _main(self):
        hid.load()
        self.ready = True

    def screenSearch(self, bitmap_template, tl_x, tl_y, br_x, br_y, path_template=None, frame=None):
        if path_template:
            path = path_template.encode('utf-8')
        else:
            path = None
        
        # start_time = time.time()
        result = self.ImageSearch(tl_x, tl_y, br_x, br_y, path,frame,bitmap_template)
        # end_time = time.time()
        # print("耗时: {:.4f}秒".format(end_time - start_time))
        array_result = str(result).split('|', -1)
        if len(array_result) == 5:
            return int(array_result[1]), int(array_result[2])
        else:
            return None
        
    def loadImage(self, str_path):
        dloadImage = self.dll.dloadImage
        dloadImage.restype = wintypes.HBITMAP
        path = str_path.encode('utf-8')
        image = self.dll.dloadImage(path, 0, 0, 0, 0)
        return image

dll_helper = DllHelper()
    

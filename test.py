
import datetime
import time
import asyncio
import threading
import cv2
import rx
from rx import Observable, operators as op
from rx.subject import Subject, BehaviorSubject
from src.common.constants import *
from src.common.dll_helper import dll_helper
from src.common.image_template import *
from src.chat_bot.wechat_bot import WechatBot
from src.common import utils
 
# debounce操作符，仅在时间间隔之外的可以发射

def thread_test():
    def task():
        start = time.time()
        time.sleep(2)
        print(f" {time.time() - start} task finished\n")
        
    t = threading.Thread(target=task)
    t.start()
    time.sleep(1)
    print(t)
    t.join()
    print(t)

def asyc_test():

    async def async_fun(fun):
        return fun()

    async def async_function(num):  # async修饰的异步函数，在该函数中可以添加await进行暂停并切换到其他异步函数中
        await asyncio.sleep(0.06)  # 当执行await future这行代码时（future对象就是被await修饰的函数），首先future检查它自身是否已经完成，如果没有完成，挂起自身，告知当前的Task（任务）等待future完成。
        return '协程花费时间：{}秒'.format(time.time() - now_time)
    
    def test():
        time.sleep(1)
        return 1
    
    now_time = time.time()  # 程序运行时的时间戳
    loop = asyncio.get_event_loop()  # 通过get_event_loop方法获取事件循环对象
    tasks = [loop.create_task(async_function(1)), loop.create_task(async_fun(test))]  # 通过事件循环的create_task方法创建任务列表
    events = asyncio.wait(tasks)  # 通过asyncio.wait(tasks)将任务收集起来

    loop.run_until_complete(events)  # 等待events运行完毕
    for task in tasks:  # 遍历循环列表，将对应任务返回值打印出来
        print(task.result())
    print('总运行花费时常：{}秒'.format(time.time() - now_time))
    loop.close()  # 结束循环



def subject_test():
    ob =  BehaviorSubject('init')
    ob.pipe(
        op.throttle_first(1)
        # op.debounce(3)
    ).subscribe(
        on_next=lambda i: print(i),
        on_completed=lambda: print('completed')
    )
    
    print('press enter to print, press other key to exit')
    while True:
        s = input()
        if s == '':
            ob.on_next(datetime.datetime.now().time())
        else:
            ob.on_completed()
            break

def minimap_to_window_test():
    '''convent the minimap point to the screen point'''
    image_path = ".test/maple_230828224432541.png"
    frame = cv2.imread(image_path)
    frame = frame[window_cap_top:-window_cap_botton, window_cap_horiz:-window_cap_horiz]

    window_width = frame.shape[1]
    window_height = frame.shape[0]
    
    c_frame = dll_helper.loadImage(image_path)
    x1 = y1 = 0
    x2 = window_width
    y2 = window_height
    tl = dll_helper.screenSearch(MM_TL_BMP, 0, 0, 300, 300, frame=c_frame)
    br = dll_helper.screenSearch(MM_BR_BMP, 0, 0, 300, 300, frame=c_frame)

    mm_tl = (
        tl[0] - x1 - 2 - window_cap_horiz + 20,
        tl[1] - y1 + 2 - window_cap_top
    )
    mm_br = (
        br[0] - x1 + 16 - window_cap_horiz - 20,
        br[1] - y1 - window_cap_top
    )
    minimap = frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]
    player = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
    point = player[0]

    # cv2.imshow('', minimap)
    # cv2.waitKey()

    mini_height, mini_width, _ = minimap.shape

    map_width = mini_width * MINIMAP_SCALE
    map_height = mini_height * MINIMAP_SCALE

    map_x = point[0] * MINIMAP_SCALE
    map_y = point[1] * MINIMAP_SCALE

    if map_x < window_width // 2:
        x = map_x
    elif map_width - map_x < window_width // 2:
        x = map_x - (map_width - window_width)
    else:
        x = window_width // 2

    if map_y < window_height // 2:
        y = map_y
    elif map_height - map_y < window_height // 2:
        y = map_y - (map_height - window_height)
    else:
        y = window_height // 2
        
    crop = frame[y:y+200, x:x+300]
    MOB_TEMPLATE_L = cv2.imread('assets/mobs/Sandblade.png', 0)
    MOB_TEMPLATE_R = cv2.flip(MOB_TEMPLATE_L, 1)
    start = time.time()
    mobs = utils.multi_match(crop, MOB_TEMPLATE_L, threshold=0.95)
    mobs = utils.multi_match(crop, MOB_TEMPLATE_R, threshold=0.95)
    print(f'{time.time() - start}')
    
    cv2.circle(frame, (x, y), 10, (0, 255, 0), 2)    
    cv2.imshow('', frame)
    cv2.waitKey()

def wechat_test():
    dll_helper.start()
    while not dll_helper.ready:
        time.sleep(0.01)
    
    chat_bot = WechatBot("yep")
    chat_bot.run()
    chat_bot.send_message("test")
    

def mob_detect_test():
    frame = cv2.imread(".test/maple_230828224432541.png")
    
    # PLAYER_SLLEE_TEMPLATE = cv2.imread('assets/roles/player_sllee_template.png', 0)
    # player_match = utils.multi_match(frame, PLAYER_SLLEE_TEMPLATE, threshold=0.9)
    # player_pos = (player_match[0][0] - 5, player_match[0][1] - 55)
    # crop = frame[player_pos[1]-180:player_pos[1]-20, player_pos[0]-300:player_pos[0]+300]
    # cv2.imshow('', crop)
    # cv2.waitKey()
    
    MOB_TEMPLATE_L = cv2.imread('assets/mobs/Seeker T-Drone Model A.png', 0)
    MOB_TEMPLATE_R = cv2.flip(MOB_TEMPLATE_L, 1)
    # h, w = MOB_TEMPLATE_L.shape
    # MOB_TEMPLATE_ELITE = cv2.resize(MOB_TEMPLATE_L, (w * 2, h * 2))
    start = time.time()
    mobs = utils.multi_match(frame, MOB_TEMPLATE_L, threshold=0.95, debug=False)
    mobs = utils.multi_match(frame, MOB_TEMPLATE_R, threshold=0.95, debug=False)
    print(f'{time.time() - start}')

if __name__ == "__main__":
    # subject_test()
    minimap_to_window_test()
    # wechat_test()
    # mob_detect_test()
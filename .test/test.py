import rx
from rx import Observable, operators as op
from rx.subject import Subject, BehaviorSubject

import datetime
 
# debounce操作符，仅在时间间隔之外的可以发射

if __name__ == "__main__":

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
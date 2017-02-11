import sys
import time
import os


WIDGETS = {"left": '[', "right": ']', "symbol1": '#', "symbol2": '='}


def progressbar(filename, total, widgets):
    while True:
        current = os.path.getsize(filename)
        out = int(current/total*30)*widgets["symbol1"] + (30 - int(current/total*30))*widgets["symbol2"]

        print("progress: ", end='')
        sys.stdout.write(widgets["left"] + out + widgets["right"])
        if current == total:
            break
        time.sleep(1)
        sys.stdout.write('\r')

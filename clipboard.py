from tkinter import Tk
tk = Tk()
import time
x = None
while True:
    t = tk.selection_get(selection="CLIPBOARD")
    if x != t:
        x = t
        print('Saved : ' + x)
        f = open('clipboard.txt', "a+")
        f.write(x + '\n')
        f.close()
    time.sleep(0.1)
import re
import wx.adv
import subprocess        
import wx
import threading
import pyperclip
import time
from pynput.mouse import Listener
from pynput import keyboard
import pyautogui
from PIL import ImageGrab, Image

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, app):
        self.frame = frame
        self.app = app

        super(TaskBarIcon, self).__init__()
        self.set_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self):
        path = "text_icon.png" if self.app.textMode else "img_icon.png"
        icon = wx.Icon(path)
        self.SetIcon(icon, "e-ink")

    def on_left_down(self, event):
        self.app.toggleMode()
        self.set_icon()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()

class App(wx.App):
    def __init__(self):
        self.textMode = True
        self.fromFile = False
        self.clipboard = ""
        self.file = open("./content", "r", encoding='utf-8').read()
        self.filePart = 0
        self.scroll = 0
        self.prevMD5 = ""
        super(App, self).__init__(False)

    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame, self)
        return True

    def toggleMode(self):
        self.textMode = not self.textMode
        self.syncMode()

    def syncMode(self):
        mode = "text" if self.textMode else "image"
        output = f'var mode = "{mode}";'
        with open('./viewer/mode.js', 'w') as file:
            file.write(output)
            file.close()
        self.updateScroll()

    def getText(self):
        text = ""
        read_len = 260

        if self.fromFile:
            # print( self.file )
            # print( self.filePart, self.filePart*read_len )
            # self.file.seek( max(self.filePart* read_len, 0) )
            fromIndex = self.filePart * read_len
            fromIndex = max(fromIndex, 0)
            text = self.file[ fromIndex : fromIndex + read_len ]
            # text = self.file.read( read_len )
        else:
            text = pyperclip.paste()

        return text

    def textModeThread(self):
        text = self.getText()
        if not text: return

        if text != self.clipboard:
            # print("Got clipboard: ", text)
            self.clipboard = text
            # remove all pdf newline
            text = re.sub(r'(?<=[^.!])\n', ' ', text)
            text = text.translate(str.maketrans({"-":  r"\-",
                                          "]":  r"\]",
                                          "\\": r"\\",
                                          "^":  r"\^",
                                          "$":  r"\$",
                                          "*":  r"\*",
                                          '"':  r"\""}))
            segs = text.split("\n")
            for i in range(len(segs)):
                segs[i] = f'"{ segs[i] }\\n"'
            
            raw = "\n +".join(segs)
            output = f'var content = {raw}'
            with open("./viewer/content.js", "w") as file:
                file.write(output)
                file.close()
            self.scroll = 0
            self.updateScroll()

    def imageModeThread(self):
        cursor = pyautogui.position()
        width = 900
        height = 880

        startX = cursor.x - width 
        startY = cursor.y - height

        endX = cursor.x + width
        endY = cursor.y + height

        screen = ImageGrab.grab(bbox=(startX, startY, endX, endY))

        fn = lambda x : 255 if x > 180 else 0
        screen = screen.convert('L').point(fn, mode='1')
        screen.save("./to_view.png", optimize=True)

        screen.close()
        output = subprocess.getoutput("md5sum ./to_view.png | cut -d ' ' -f 1")
        print( output )
        if output != self.prevMD5:
            self.prevMD5 = output
            subprocess.getoutput("mv ./to_view.png ./viewer/res.png")

    def CheckLoop(self):
        while True:
            if self.textMode:
                self.textModeThread()
                time.sleep(0.1)
            else:
                self.imageModeThread()
                time.sleep(2)

    def listenScroll(self):
        def on_scroll(x, y, dx, dy):
            self.filePart -= dy

        with Listener(on_scroll=on_scroll) as listener:
            listener.join()
        
    def updateScroll(self):
        with open("./viewer/scroll.js", "w") as file:
            output = f"var scroll = {self.scroll};";
            file.write(output)

    def listenKeydown(self):
        def on_press(key):
            try:
                k = key.char  # single-char keys
            except:
                k = key.name  # other keys
            
            if k in ["left", "right"]:
                print( k )

            if k == "left":
                self.scroll = max(0, self.scroll-1 )
                self.updateScroll()
            elif k == "right":
                self.scroll += 1
                self.updateScroll()

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        listener.join()


def main():
    app = App()
    threading.Thread(target=app.MainLoop).start()
    threading.Thread(target=app.listenScroll).start()
    threading.Thread(target=app.listenKeydown).start()
    app.syncMode()
    app.CheckLoop()

if __name__ == '__main__':
    main()
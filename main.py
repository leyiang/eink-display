#!/usr/bin/env python

import re
import os
import sys
import wx.adv
import subprocess
import wx
import threading
import pyperclip
import time
from pynput.mouse import Listener
from PIL import ImageGrab, Image
from modules.ConfigManager import ConfigManager
from modules.KeyEvent import KeyEvent
from modules.SizeManager import SizeManager
from modules.WireManager import WireManager
from modules.mouse import getCursorInfo

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
        create_menu_item(menu, 'Toggle Capture', self.app.toggle_capture)
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self):
        path = "./assets/text_icon.png" if self.app.textMode else "./assets/img_icon.png"
        icon = wx.Icon(path)
        self.SetIcon(icon, "e-ink")

    def on_left_down(self, event):
        self.app.toggleMode()
        self.set_icon()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()
        self.app.on_exit()
        os._exit(0)

class App(wx.App):
    def __init__(self):
        self.fromFile = False
        self.config = ConfigManager()

        self.textMode = (
            self.config.get("mode", "text") == "text"
        )

        self.size = SizeManager()
        self.wire = WireManager( self.size )
        self.clipboard = ""
        self.file = open("./content", "r", encoding='utf-8').read()
        self.filePart = 0
        self.captureMode = True
        self.scroll = 0
        self.prevMD5 = ""
        self.server = subprocess.Popen(["live-server", "./viewer", "--no-browser"], stdout=subprocess.DEVNULL)
        self.prevCursor = ""
        self.keyListener = KeyEvent()
        super(App, self).__init__(False)

    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame, self)
        return True

    def on_exit(self):
        self.server.kill()

    def toggle_capture(self, a):
        self.captureMode = not self.captureMode
        if self.captureMode:
            self.wire.showWire()
        else:
            self.wire.hideWire()

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

        print("Sync mode run")
        if not self.textMode:
            self.wire.showWire()
        else:
            self.wire.hideWire()

        self.config.update("mode", mode)

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
            print("Got clipboard: ", text)
            self.clipboard = text
            # remove all pdf newline
            text = re.sub(r'(?<=[^.!。：])\n', ' ', text)
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
            
            raw = "\n\n +".join(segs)
            output = f'var content = {raw}'
            with open("./viewer/content.js", "w") as file:
                file.write(output)
                file.close()
            self.scroll = 0
            self.updateScroll()

    def updateImage(self, x, y):
        startX = x - self.size.w 
        startY = y - self.size.h

        endX = x + self.size.w
        endY = y + self.size.h

        screen = ImageGrab.grab(bbox=(startX, startY, endX, endY))
        
        fn = lambda x : 255 if x > 180 else 0
        screen = screen.convert('L').point(fn, mode='1')

        screen.save("./assets/to_view.png", optimize=True)
        screen.close()
        subprocess.getoutput("mv ./assets/to_view.png ./viewer/res.png")
        print("Time: ", time.time())

    def refreshImage(self):
        subprocess.getoutput("cp ./viewer/res.png ./viewer/tmp.png")

        fn = lambda x : 0
        img = Image.new(mode="RGB", size=(2600, 1600))
        img = img.convert("L").point(fn, mode="1")
        img.save("./viewer/res.png", optimize=True)
        img.close()
        time.sleep(.16)
        subprocess.getoutput("mv ./viewer/tmp.png ./viewer/res.png")


    def refreshText(self):
        self.toggleMode()

        fn = lambda x : 0
        img = Image.new(mode="RGB", size=(2600, 1600))
        img = img.convert("L").point(fn, mode="1")
        img.save("./viewer/res.png", optimize=True)
        img.close()
        time.sleep(.16)

        # fn = lambda x : 1
        # img = Image.new(mode="RGB", size=(2600, 1600))
        # img = img.convert("L").point(fn, mode="1")
        # img.save("./viewer/res.png", optimize=True)
        # img.close()
        #
        # time.sleep(.16)
        self.toggleMode()

    def refresh(self):
        if self.textMode:
            self.refreshText()
        else:
            self.refreshImage()

    def imageModeThread(self):
        info = getCursorInfo()
        if info == None: return
        [x, y] = info
        cursorKey = f"{x}_{y}"

        if cursorKey == self.prevCursor:
            return

        self.prevCursor = cursorKey
        self.x = x
        self.y = y
        self.updateImage(x, y)
        
    def CheckLoop(self):
        while True:
            if not self.captureMode:
                time.sleep(0.1)
                continue
            if self.textMode:
                self.textModeThread()
            else:
                pass
                # draw image while mouse click
                # stop auto draw
                # self.imageModeThread()
            time.sleep(0.1)

    def listenScroll(self):
        def on_click(x, y, button, *_args):
            if not self.captureMode: return

            btn = button.name
            if btn in ["left", "middle"]:
                if not self.textMode:
                    self.updateImage(x, y)

        def on_scroll(x, y, dx, dy):
            self.filePart -= dy

        with Listener(on_scroll=on_scroll, on_click=on_click) as listener:
            listener.join()
        
    def updateScroll(self):
        with open("./viewer/scroll.js", "w") as file:
            output = f"var scroll = {self.scroll};";
            file.write(output)

    def updateRegion(self):
        while True:
            if self.wire and self.wire.wire:
                if self.textMode:
                    self.wire.hideWire()
                else:
                    [x, y] = getCursorInfo()
                    if self.wire and self.wire.wire:
                        self.wire.wire.updatePos(x, y)
            time.sleep(0.01)
        
    def init(self):
        self.syncMode()
        self.registerKeyEvents()
    
    def scrollUp(self):
        self.scroll = max(0, self.scroll-1 )
        self.updateScroll()

    def scrollDown(self):
        self.scroll += 1
        self.updateScroll()

    def shrinkCaptureRegion(self):
        if self.textMode: return
        self.size.shrink()
        self.wire.updateSize()

    def expandCaptureRegion(self):
        if self.textMode: return
        self.size.expand()
        self.wire.updateSize()

    def redrawImage(self):
        if not self.textMode:
            self.updateImage(
                self.x,
                self.y,
            )
        
    def shrinkRatio(self):
        if self.textMode: return
        self.size.shrinkRatio()
        self.wire.updateSize()

    def expandRatio(self):
        if self.textMode: return
        self.size.expandRatio()
        self.wire.updateSize()

    def registerKeyEvents(self):
        self.keyListener.on("left", self.scrollUp)
        self.keyListener.on("right", self.scrollDown)
        # self.keyListener.on("2", self.redrawImage)
        self.keyListener.on("5", self.refresh)

        self.keyListener.on("[", self.shrinkCaptureRegion)
        self.keyListener.on("]", self.expandCaptureRegion)

        self.keyListener.on("9", self.shrinkRatio)
        self.keyListener.on("0", self.expandRatio)

        
def main():
    app = App()

    # def done():
    #     os._exit(0)

    # app.keyListener.on("0", done)

    threading.Thread(target=app.MainLoop).start()
    threading.Thread(target=app.listenScroll).start()
    threading.Thread(target=app.updateRegion).start()
    app.init()
    app.CheckLoop()

if __name__ == '__main__':
    os.chdir( sys.argv[1] )
    main()

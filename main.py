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
from modules.PipeManager import PipeManager
from modules.mouse import getCursorInfo
from modules.utils import debounce

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

def notify(message, tag):
    notify_id = {"eink-thresh": 11}[tag]
    subprocess.run(["notify-send", "-r", str(notify_id), "E-ink Threshold", message], check=False)

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
        create_menu_item(menu, 'Select Area', self.app.select_area)
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self):
        path = "./assets/wrong.png" if self.app.stop else "./assets/img_icon.png"
        icon = wx.Icon(path)
        self.SetIcon(icon, "e-ink")

    def on_left_down(self, event):
        # self.app.toggleMode()
        self.icon.setIcon()
        self.app.toggleStop()
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

        # self.textMode = (
        #     self.config.get("mode", "text") == "text"
        # )

        self.textMode = False

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

        self.stop = False
        self.icon = None

        self.thresh = 180
        self.x = 0
        self.y = 0
        self.pipe_manager = PipeManager()
        super(App, self).__init__(False)

    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        self.icon = TaskBarIcon(frame, self)
        return True

    def on_exit(self):
        self.server.kill()
        # Clean up pipes
        self.pipe_manager.stop_listening()
        self.pipe_manager.cleanup_pipes()

    def toggle_capture(self):
        if self.stop:
            return

        self.captureMode = not self.captureMode
        if self.captureMode:
            self.wire.showWire()
        else:
            self.wire.hideWire()

    def toggleStop(self):
        self.stop = not self.stop
        self.icon.set_icon()

        if self.stop:
            self.captureMode = False
            self.wire.hideWire()
        else:
            self.captureMode = True
            self.wire.showWire()

    def toggleMode(self):
        self.textMode = not self.textMode
        if not self.captureMode:
            self.toggle_capture()
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
            text = re.sub(r'-\s*\n', '', text)

            # TODO
            # 英文文本PDF中的换行,要替换成空格
            # 中文文本PDF中的换行,要替换成空字符串

            text = re.sub(r'(?<=[^.!。！：:："")])\n', ' ', text)
            text = text.translate(str.maketrans({"-":  r"\-",
                                          "]":  r"\]",
                                          "\\": r"\\",
                                          "^":  r"\^",
                                          "$":  r"\$",
                                          "*":  r"\*",
                                          '"':  r"\""}))
            segs = text.split("\n")
            for i in range(len(segs)):
                segs[i] = f'"<p>{ segs[i] }</p>"'

            raw = "\n\n +".join(segs)
            output = f'var content = {raw}'
            with open("./viewer/content.js", "w") as file:
                file.write(output)
                file.close()
            self.scroll = 0
            self.updateScroll()

            # self.refreshText()

    def display_image(self, image):
        image.save("./assets/to_view.png", optimize=True)
        subprocess.getoutput("mv ./assets/to_view.png ./viewer/res.png")

    def get_bw_image(self, image):
        fn = lambda x : 255 if x > self.thresh else 0
        return image.convert('L').point(fn, mode='1')

    def updateImage(self, x, y):
        startX = x - self.size.w
        startY = y - self.size.h

        endX = x + self.size.w
        endY = y + self.size.h

        screen = ImageGrab.grab(bbox=(startX, startY, endX, endY))

        w,h = screen.size
        bw = 3 # border width
        rm_border = screen.crop((bw,bw,w-bw, h-bw))
        rm_border.save("./viewer/raw.png")

        bw_screen = self.get_bw_image( screen )
        self.display_image( bw_screen )

        screen.close()
        bw_screen.close()

    def refreshImage(self):
        subprocess.getoutput("cp ./viewer/res.png ./viewer/tmp.png")

        fn = lambda x : 0
        img = Image.new(mode="RGB", size=(2600, 1600))
        img = img.convert("L").point(fn, mode="1")
        img.save("./viewer/res.png", optimize=True)
        img.close()

        time.sleep(.5)
        subprocess.getoutput("cp ./viewer/tmp.png ./viewer/res.png")


    @debounce(.05)
    def refreshText(self):
        self.toggleMode()

        fn = lambda x : 0
        img = Image.new(mode="RGB", size=(2600, 1600))
        img = img.convert("L").point(fn, mode="1")
        img.save("./viewer/res.png", optimize=True)
        img.close()

        time.sleep(.5)

        # fn = lambda x : 1
        # img = Image.new(mode="RGB", size=(2600, 1600))
        # img = img.convert("L").point(fn, mode="1")
        # img.save("./viewer/res.png", optimize=True)
        # img.close()
        #
        # time.sleep(.16)
        self.textMode = True
        self.syncMode()

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
                    self.refreshImage()

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
        self.setup_pipe_commands()

    def scrollUp(self):
        self.scroll = max(0, self.scroll-1 )
        self.updateScroll()

    def scrollDown(self):
        self.scroll += 1
        self.updateScroll()

    def shrinkCaptureRegion(self):
        if self.stop: return
        if self.textMode: return
        if not self.captureMode: return

        self.size.shrink()
        self.wire.updateSize()

    def expandCaptureRegion(self):
        if self.stop: return
        if self.textMode: return
        if not self.captureMode: return

        self.size.expand()
        self.wire.updateSize()

    def redrawImage(self):
        if not self.textMode:
            if hasattr(self, 'x') and hasattr(self, 'y'):
                self.updateImage(self.x, self.y)
            else:
                info = getCursorInfo()
                if info:
                    x, y = info
                    self.updateImage(x, y)

    def reprocess_with_thresh(self):
        """重新处理现有图像，使用当前阈值"""
        try:
            # 从保存的原图重新应用阈值
            raw_image = Image.open("./viewer/raw.png")
            bw_image = self.get_bw_image(raw_image)
            self.display_image(bw_image)
            raw_image.close()
            bw_image.close()
            print(f"Reprocessed image with threshold: {self.thresh}")
        except FileNotFoundError:
            print("No raw image found, capturing new image")
            # 如果没有原图，则重新捕获
            self.redrawImage()
        except Exception as e:
            print(f"Error reprocessing image: {e}")
            # 如果处理失败，尝试重新捕获
            self.redrawImage()

    def shrinkRatio(self):
        if self.stop: return
        if self.textMode: return
        if not self.captureMode: return

        self.size.shrinkRatio()
        self.wire.updateSize()

    def expandRatio(self):
        if self.stop: return
        if self.textMode: return
        if not self.captureMode: return

        self.size.expandRatio()
        self.wire.updateSize()

    def expandThresh(self):
        self.thresh += 10
        print( self.thresh )
        notify(f"Threshold: {self.thresh} (+10)", "eink-thresh")
        self.reprocess_with_thresh()
        # Update status for interactive display
        self.pipe_manager.write_status(f"thresh:{self.thresh}")

    def toggleThresh(self):
        if self.thresh > 150:
            self.thresh = 120
        else:
            self.thresh = 180
        print( self.thresh )
        notify(f"Threshold: {self.thresh} (toggled)", "eink-thresh")
        self.reprocess_with_thresh()
        # Update status for interactive display
        self.pipe_manager.write_status(f"thresh:{self.thresh}")

    def shrinkThresh(self):
        self.thresh -= 10
        print( self.thresh )
        notify(f"Threshold: {self.thresh} (-10)", "eink-thresh")
        self.reprocess_with_thresh()
        # Update status for interactive display
        self.pipe_manager.write_status(f"thresh:{self.thresh}")

    def registerKeyEvents(self):
        # self.keyListener.on("left", self.scrollUp)
        # self.keyListener.on("right", self.scrollDown)
        # self.keyListener.on("2", self.redrawImage)
        self.keyListener.on("5", self.refresh)

        self.keyListener.on("[", self.shrinkCaptureRegion)
        self.keyListener.on("]", self.expandCaptureRegion)

        # 主要用rofi+pipe来修改了，不用键盘了（太容易冲突）
        # self.keyListener.on("-", self.shrinkThresh)
        # self.keyListener.on("=", self.expandThresh)
        # self.keyListener.on("print_screen", self.toggleThresh)

        self.keyListener.on("9", self.shrinkRatio)
        self.keyListener.on("0", self.expandRatio)

        self.keyListener.on("`", self.toggle_capture)
        self.keyListener.on("~", self.toggleStop)
        self.keyListener.on("scroll_lock", self.toggleStop)
        # self.keyListener.on("print_screen", self.redrawImage)
        # "pause" key not used

        self.keyListener.on("f7", self.wire.start_area_selection)
        self.keyListener.on("f8", self.open_rofi_menu)

    def select_area(self, _event):
        try:
            # 使用完整路径调用系统的flameshot，限制在第一个屏幕
            result = subprocess.run(
                ["/usr/bin/slop", "-f", "%x %y %w %h"],
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )

            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                print(output)
                [x, y, w, h] = output.split(" ")

                # 将字符串转换为整数，并设置为捕获区域的半宽半高
                width = int(w) // 2
                height = int(h) // 2

                self.size.setWidth(width)
                self.size.setHeight(height)

                self.wire.updateSize()
                print(f"已更新捕获区域大小: {width}x{height}")
            else:
                print("slop选择被取消或失败")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
        except Exception as e:
            print(f"调用slop时出错: {e}")

    def open_rofi_menu(self):
        """打开rofi设置菜单"""
        try:
            script_path = os.path.join(os.getcwd(), "eink_rofi_interactive.py")
            subprocess.Popen([script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"打开rofi菜单时出错: {e}")

    def create_command_pipe(self):
        """创建命名管道用于接收rofi命令"""
        if os.path.exists(self.pipe_path):
            os.unlink(self.pipe_path)
        if os.path.exists(self.status_path):
            os.unlink(self.status_path)
        os.mkfifo(self.pipe_path)
        os.mkfifo(self.status_path)
        print(f"Created command pipe: {self.pipe_path}")
        print(f"Created status pipe: {self.status_path}")

    def listen_for_commands(self):
        """监听来自命名管道的命令"""
        pipe_fd = None
        try:
            # Open pipe once outside the loop
            pipe_fd = os.open(self.pipe_path, os.O_RDONLY | os.O_NONBLOCK)
            print(f"Opened pipe for listening: {self.pipe_path}")

            while True:
                try:
                    # Use select to check if data is available
                    ready, _, _ = select.select([pipe_fd], [], [], 0.1)
                    if ready:
                        data = os.read(pipe_fd, 1024).decode('utf-8')
                        if data:
                            # Process each line as a separate command
                            for line in data.strip().split('\n'):
                                command = line.strip()
                                if command:
                                    self.process_command(command)
                    time.sleep(0.01)  # Very short sleep for responsiveness

                except OSError as e:
                    if e.errno == 11:  # EAGAIN - no data available
                        time.sleep(0.1)
                        continue
                    else:
                        raise e

        except Exception as e:
            print(f"Error in command listener: {e}")
        finally:
            if pipe_fd is not None:
                try:
                    os.close(pipe_fd)
                    print("Closed command pipe")
                except:
                    pass

    def process_command(self, command):
        """处理接收到的命令"""
        print(f"Received command: {command}")
        command_map = {
            "thresh_up": self.expandThresh,
            "thresh_down": self.shrinkThresh,
            "thresh_toggle": self.toggleThresh,
            "size_up": self.expandCaptureRegion,
            "size_down": self.shrinkCaptureRegion,
            "ratio_up": self.expandRatio,
            "ratio_down": self.shrinkRatio,
            "toggle_capture": self.toggle_capture,
            "toggle_stop": self.toggleStop,
            "refresh": self.refresh,
            "select_area": lambda: self.select_area(None),
            "get_thresh": self.get_thresh,
            "get_size": self.get_size,
            "get_ratio": self.get_ratio
        }

        if command in command_map:
            command_map[command]()
        else:
            print(f"Unknown command: {command}")

    def get_thresh(self):
        """获取当前阈值"""
        self.pipe_manager.write_status(f"thresh:{self.thresh}")

    def get_size(self):
        """获取当前大小"""
        self.pipe_manager.write_status(f"size:{self.size.w}x{self.size.h}")

    def get_ratio(self):
        """获取当前比例"""
        self.pipe_manager.write_status(f"ratio:{self.size.ratio}")

    def setup_pipe_commands(self):
        """设置管道命令处理器"""
        command_map = {
            "thresh_up": self.expandThresh,
            "thresh_down": self.shrinkThresh,
            "thresh_toggle": self.toggleThresh,
            "size_up": self.expandCaptureRegion,
            "size_down": self.shrinkCaptureRegion,
            "ratio_up": self.expandRatio,
            "ratio_down": self.shrinkRatio,
            "toggle_capture": self.toggle_capture,
            "toggle_stop": self.toggleStop,
            "refresh": self.refresh,
            "select_area": lambda: self.select_area(None),
            "get_thresh": self.get_thresh,
            "get_size": self.get_size,
            "get_ratio": self.get_ratio
        }
        self.pipe_manager.register_commands(command_map)

def main():
    app = App()

    # def done():
    #     os._exit(0)

    # app.keyListener.on("0", done)

    threading.Thread(target=app.MainLoop).start()
    threading.Thread(target=app.listenScroll).start()
    threading.Thread(target=app.updateRegion).start()

    # Create command pipe and start command listener
    app.pipe_manager.create_pipes()
    app.init()
    app.pipe_manager.start_listening()

    app.CheckLoop()


if __name__ == '__main__':
    os.chdir( sys.argv[1] )
    main()

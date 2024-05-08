from modules.wire import createOutlineWindow
import threading

class WireManager():
    def __init__(self):
        self.wire = None
        self.thread = None
        self.stop = False
    
    def showWire(self):
        self.wire = createOutlineWindow(0, 0, 100, 100)
        self.thread = threading.Thread(target=self.wire.loop, args=(1, lambda: self.stop))
        self.stop = False
        self.thread.start()
        
    def hideWire(self):
        self.wire.window.destroy()
        self.stop = True
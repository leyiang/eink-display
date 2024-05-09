from modules.wire import createOutlineWindow
import threading

class WireManager():
    def __init__(self, size):
        self.wire = None
        self.thread = None
        self.stop = False
        self.size = size
    
    def showWire(self):
        print( self.size.w, self.size.h )
        self.wire = createOutlineWindow( 2*self.size.w, 2*self.size.h )
        self.thread = threading.Thread(target=self.wire.loop, args=(1, lambda: self.stop))
        self.stop = False
        self.thread.start()
        
    def hideWire(self):
        self.wire.destroy()
        self.stop = True
    
    def updateSize(self):
        self.hideWire()
        self.showWire()
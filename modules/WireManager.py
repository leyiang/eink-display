from modules.wire import createOutlineWindow
import threading

class WireManager():
    def __init__(self, size):
        self.wire = None
        self.size = size
    
    def showWire(self):
        print( self.size.w, self.size.h )
        self.wire = createOutlineWindow( 2*self.size.w, 2*self.size.h )
        
    def hideWire(self):
        if self.wire:
            # self.wire.window.clear_area(0, 0, 4000, 4000)
            self.wire.window.destroy()
            self.wire.d.flush()
        self.wire = None
   
    def updateSize(self):
        self.hideWire()
        self.showWire()
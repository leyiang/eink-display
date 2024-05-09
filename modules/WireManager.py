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
        self.wire.destroy()
    
    def updateSize(self):
        self.hideWire()
        self.showWire()
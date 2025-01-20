from modules.wire import createOutlineWindow
import threading

class WireManager():
    def __init__(self, size):
        self.wire = None
        self.size = size
        self._lock = threading.Lock()
    
    def showWire(self):
        with self._lock:
            if self.wire is None:  # Only create if there isn't one
                print(self.size.w, self.size.h)
                self.wire = createOutlineWindow(2*self.size.w, 2*self.size.h)
        
    def hideWire(self):
        with self._lock:
            if self.wire:
                try:
                    self.wire.destroy()
                except Exception as e:
                    print(f"Error destroying wire window: {e}")
                finally:
                    self.wire = None
   
    def updateSize(self):
        # First destroy the old window
        self.hideWire()
        # Then create new window with updated size
        self.showWire()
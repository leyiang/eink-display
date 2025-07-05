import threading
import time
from pynput import keyboard

class KeyEvent():
    def __init__(self) -> None:
        threading.Thread(target=self.listen).start()
        self.keyMaps = {}
        self.doubleTapMaps = {}
        self.lastKeyTime = {}
        self.doubleTapWindow = 0.3  # 300ms window for double tap
        pass

    def on_press(self, key):
        try:
            k = key.char  # single-char keys
        except:
            k = key.name  # other keys

        current_time = time.time()
        
        # Handle double tap detection
        if k in self.doubleTapMaps:
            if k in self.lastKeyTime:
                time_diff = current_time - self.lastKeyTime[k]
                if time_diff <= self.doubleTapWindow:
                    print("Double tap detected: ", k)
                    for callback in self.doubleTapMaps[k]:
                        callback()
                    # Reset the timer to prevent triple tap
                    self.lastKeyTime[k] = 0
                    return
            
            self.lastKeyTime[k] = current_time

        if k in self.keyMaps:
            print("Keydown: ", k)

            for callback in self.keyMaps[k]:
                callback()
    
    def on(self, key, callback):
        if key not in self.keyMaps:
            self.keyMaps[key] = []
        self.keyMaps[key].append( callback )
    
    def onDoubleTap(self, key, callback):
        if key not in self.doubleTapMaps:
            self.doubleTapMaps[key] = []
        self.doubleTapMaps[key].append( callback )
    
    def listen(self):
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        listener.join()
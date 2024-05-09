import threading
from pynput import keyboard

class KeyEvent():
    def __init__(self) -> None:
        threading.Thread(target=self.listen).start()
        self.keyMaps = {}
        pass

    def on_press(self, key):
        try:
            k = key.char  # single-char keys
        except:
            k = key.name  # other keys
        
        if k in self.keyMaps:
            print("Keydown: ", k)

            for callback in self.keyMaps[k]:
                callback()
    
    def on(self, key, callback):
        if key not in self.keyMaps:
            self.keyMaps[key] = []
        self.keyMaps[key].append( callback )
    
    def listen(self):
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        listener.join()
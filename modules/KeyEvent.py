import threading
import time
from pynput import keyboard

class KeyEvent():
    def __init__(self) -> None:
        threading.Thread(target=self.listen).start()
        self.keyMaps = {}
        self.doubleTapMaps = {}
        self.comboMaps = {}
        self.lastKeyTime = {}
        self.doubleTapWindow = 0.3  # 300ms window for double tap
        self.pressed_keys = set()
        pass

    def on_press(self, key):
        try:
            k = key.char.lower() if key.char else None  # single-char keys, normalize to lowercase
        except:
            k = getattr(key, 'name', str(key))  # other keys, handle KeyCode objects

        if k:
            self.pressed_keys.add(k)
        
        current_time = time.time()

        # Handle combo keys
        for combo_key, callbacks in self.comboMaps.items():
            if self.is_combo_pressed(combo_key):
                print(f"Combo pressed: {combo_key}")
                for callback in callbacks:
                    callback()

        # Handle double tap detection
        if k and k in self.doubleTapMaps:
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

        if k and k in self.keyMaps:
            print("Keydown: ", k)

            for callback in self.keyMaps[k]:
                callback()

    def on_release(self, key):
        try:
            k = key.char.lower() if key.char else None  # single-char keys, normalize to lowercase
        except:
            k = getattr(key, 'name', str(key))  # other keys, handle KeyCode objects

        if k:
            self.pressed_keys.discard(k)

    def is_combo_pressed(self, combo_key):
        """Check if a combo key is pressed"""
        keys = combo_key.split("+")
        for key in keys:
            key = key.strip().lower()
            # Handle alt key mapping
            if key == "alt":
                alt_pressed = ("alt_l" in self.pressed_keys or "alt_r" in self.pressed_keys or "alt" in self.pressed_keys)
                if not alt_pressed:
                    return False
            # Handle shift key mapping  
            elif key == "shift":
                shift_pressed = ("shift" in self.pressed_keys or "shift_r" in self.pressed_keys)
                if not shift_pressed:
                    return False
            # Handle ctrl key mapping
            elif key == "ctrl":
                ctrl_pressed = ("ctrl_l" in self.pressed_keys or "ctrl_r" in self.pressed_keys)
                if not ctrl_pressed:
                    return False
            else:
                key_pressed = key in self.pressed_keys
                if not key_pressed:
                    return False
        return True

    def on(self, key, callback):
        if key not in self.keyMaps:
            self.keyMaps[key] = []
        self.keyMaps[key].append( callback )

    def onDoubleTap(self, key, callback):
        if key not in self.doubleTapMaps:
            self.doubleTapMaps[key] = []
        self.doubleTapMaps[key].append( callback )

    def onCombo(self, combo_key, callback):
        if combo_key not in self.comboMaps:
            self.comboMaps[combo_key] = []
        self.comboMaps[combo_key].append( callback )

    def listen(self):
        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()
        listener.join()
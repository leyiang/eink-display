from modules.wire import createOutlineWindow
from modules.SelectionWindow import SelectionWindow
import threading
from PIL import ImageGrab, Image
import wx
import time
import subprocess

class WireManager():
    def __init__(self, size):
        self.wire = None
        self.size = size
        self._lock = threading.Lock()
        self.selection_window = None
    
    def get_active_window_screenshot(self):
        """Get screenshot of only the active window using scrot"""
        try:
            # Capture active window to a temporary file
            temp_file = "/tmp/temp_screenshot.png"
            result = subprocess.run(["scrot", "-u", temp_file], capture_output=True)
            
            if result.returncode != 0:
                print("Failed to capture with scrot:", result.stderr)
                return None
                
            # Open the captured image
            screenshot = Image.open(temp_file)
            
            # Clean up temp file
            subprocess.run(["rm", temp_file])
            
            return screenshot
            
        except Exception as e:
            print(f"Error capturing active window: {e}")
            return None
        
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
        
    def on_area_selected(self, width, height):
        # Update size manager with new dimensions
        self.size.w = width // 2
        self.size.h = height // 2
        # Update wire window
        self.updateSize()
        
    def start_area_selection(self):
        # Hide the wire window before taking screenshot
        was_visible = self.wire is not None
        if was_visible:
            self.hideWire()
            time.sleep(0.1)
        
        try:
            # Capture active window instead of full screen
            screenshot = self.get_active_window_screenshot()
            if screenshot is None:
                print("Failed to capture active window, falling back to full screen")
                screenshot = ImageGrab.grab()
            
            # Create selection window in the main thread
            wx.CallAfter(self._create_selection_window, screenshot, was_visible)
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            if was_visible:
                self.showWire()
        
    def _create_selection_window(self, screenshot, restore_wire=False):
        self.selection_window = SelectionWindow(screenshot, 
            lambda w, h: self._handle_selection(w, h, restore_wire))
        
    def _handle_selection(self, width, height, restore_wire):
        self.on_area_selected(width, height)
        if not restore_wire:
            self.hideWire()
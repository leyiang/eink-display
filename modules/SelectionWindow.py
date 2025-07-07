import wx
import threading
from PIL import Image
import numpy as np

class SelectionWindow(wx.Frame):
    def __init__(self, screenshot, callback):
        self.screenshot = screenshot
        self.callback = callback

        # Get screen size
        display = wx.Display()
        screen_width, screen_height = display.GetGeometry().GetSize()

        # Scale image to fit screen while maintaining aspect ratio
        img_width, img_height = screenshot.size
        scale = min(screen_width/img_width, screen_height/img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # Resize the screenshot
        resized_screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert PIL image to wx.Bitmap
        wx_image = wx.Bitmap.FromBuffer(new_width, new_height,
            np.array(resized_screenshot.convert('RGB')))

        style = wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.FRAME_SHAPED
        super().__init__(None, style=style)

        self.SetSize(new_width, new_height)
        # Center the window on screen
        self.SetPosition(((screen_width - new_width)//2, (screen_height - new_height)//2))

        # Store scale factor for callback
        self.scale_factor = 1/scale

        # Initialize selection coordinates
        self.start_pos = None
        self.current_pos = None
        self.selecting = False

        # Create transparent overlay
        self.overlay = wx.Overlay()

        # Bind mouse events
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)

        # Store the background
        self.background = wx_image

        # Show fullscreen
        self.ShowFullScreen(True)

    def on_key(self, event):
        # Allow ESC to cancel
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Destroy()
        event.Skip()

    def on_left_down(self, event):
        self.start_pos = event.GetPosition()
        self.selecting = True
        self.CaptureMouse()

    def on_left_up(self, event):
        if self.selecting:
            self.selecting = False
            if self.HasCapture():
                self.ReleaseMouse()

            # Calculate selection rectangle
            if self.start_pos and self.current_pos:
                x1, y1 = self.start_pos
                x2, y2 = self.current_pos
                width = abs(x2 - x1)
                height = abs(y2 - y1)

                # Only process if we have a valid selection
                if width > 10 and height > 10:
                    # Scale back to original image dimensions
                    real_width = int(width * self.scale_factor)
                    real_height = int(height * self.scale_factor)
                    self.callback(real_width, real_height)

            self.Destroy()

    def on_motion(self, event):
        if self.selecting:
            self.current_pos = event.GetPosition()
            self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.background, 0, 0)

        if self.selecting and self.start_pos and self.current_pos:
            dc = wx.ClientDC(self)
            odc = wx.DCOverlay(self.overlay, dc)
            odc.Clear()

            # Draw semi-transparent overlay
            dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 2))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)

            x1, y1 = self.start_pos
            x2, y2 = self.current_pos
            dc.DrawRectangle(min(x1, x2), min(y1, y2),
                           abs(x2 - x1), abs(y2 - y1))

            del odc
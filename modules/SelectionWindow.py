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
        self.SetPosition(((screen_width - new_width)//2, (screen_height - new_height)//2))
        
        self.scale_factor = 1/scale
        
        # Create panel and bind all events
        self.panel = wx.Panel(self, size=(new_width, new_height))
        self.panel.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        
        # Bind all events to panel
        self.panel.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.panel.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.panel.Bind(wx.EVT_MOTION, self.on_motion)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)
        
        # Initialize selection coordinates
        self.start_pos = None
        self.current_pos = None
        self.selecting = False
        
        self.overlay = wx.Overlay()
        self.background = wx_image
        self.font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        # Create a sizer to ensure panel fills the frame
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.ShowFullScreen(True)
        
    def on_key(self, event):
        key_code = event.GetKeyCode()
        if key_code in [wx.WXK_ESCAPE, ord('Q'), ord('q')]:
            self.selecting = False
            if self.panel.HasCapture():
                self.panel.ReleaseMouse()
            wx.CallAfter(self.Destroy)
            return
        event.Skip()

    def draw_instructions(self, dc):
        dc.SetFont(self.font)
        dc.SetTextForeground(wx.Colour(255, 255, 255))  # White text
        dc.SetTextBackground(wx.Colour(0, 0, 0))  # Black background
        dc.SetBackgroundMode(wx.SOLID)
        
        instructions = "ESC to cancel, Click and drag to select area"
        if self.selecting and self.start_pos and self.current_pos:
            width = abs(self.current_pos[0] - self.start_pos[0])
            height = abs(self.current_pos[1] - self.start_pos[1])
            instructions = f"Selection size: {width} x {height}"
            
        # Draw text with background
        dc.DrawText(instructions, 10, 10)
        
    def on_left_down(self, event):
        self.start_pos = event.GetPosition()
        self.selecting = True
        self.panel.CaptureMouse()
        event.Skip()
        
    def on_left_up(self, event):
        if self.selecting:
            self.selecting = False
            if self.panel.HasCapture():
                self.panel.ReleaseMouse()
            
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
        event.Skip()
            
    def on_motion(self, event):
        if self.selecting:
            self.current_pos = event.GetPosition()
            self.panel.Refresh()
        event.Skip()
            
    def on_paint(self, event):
        dc = wx.PaintDC(self.panel)
        dc.DrawBitmap(self.background, 0, 0)
        
        if self.selecting and self.start_pos and self.current_pos:
            dc = wx.ClientDC(self.panel)
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
        
        self.draw_instructions(dc) 
#!/usr/bin/python

import Xlib.threaded
from Xlib import X, display, Xutil
from Xlib.ext import shape
from ewmh import EWMH

from modules.mouse import getCursorInfo


class OutlineWindow:
    def __init__(self, display, x, y, w, h, lw=3):
        self.w = w
        self.h =h 

        self.d = display
        self.screen = self.d.screen()

        self.WM_DELETE_WINDOW = self.d.intern_atom('WM_DELETE_WINDOW')
        self.WM_PROTOCOLS = self.d.intern_atom('WM_PROTOCOLS')

        # Creates a pixel map that will be used to draw the areas that aren't masked
        bgpm = self.screen.root.create_pixmap(1, 1, self.screen.root_depth)

        # In my case I chose the color of the rectangle to be red.
        bggc = self.screen.root.create_gc(
            foreground=0xff0000,
            background=self.screen.black_pixel
        )

        # we fill the pixel map with red 
        bgpm.fill_rectangle(bggc, 0, 0, 1, 1)
        geometry = self.screen.root.get_geometry()

        self.window = self.screen.root.create_window(
                100,
                200, # y
                geometry.width, # width
                geometry.height, # height
                0, # border_width
                self.screen.root_depth, # depth
                X.InputOutput, # window_class
                X.CopyFromParent, # visual
                background_pixmap=bgpm, # attr
                event_mask=X.StructureNotifyMask, # attr
                colormap=X.CopyFromParent, # attr
                override_redirect=True # attr
        )

        # We want to make sure we're notified of window destruction so we need to enable this protocol
        self.window.set_wm_protocols([self.WM_DELETE_WINDOW])
        self.window.set_wm_hints(flags=Xutil.StateHint, initial_state=Xutil.NormalState)

        # Create an outer rectangle that will be the outer edge of the visible rectangle
        outer_rect = self.window.create_pixmap(w, h, 1)
        gc = outer_rect.create_gc(foreground=1, background=0)
        # coordinates within the graphical context are always relative to itself - not the screen!
        outer_rect.fill_rectangle(gc, 0, 0, w, h)
        gc.free()

        # Create an inner rectangle that is slightly smaller to represent the inner edge of the rectangle
        inner_rect = self.window.create_pixmap(w - (lw * 2), h - (lw * 2), 1)
        gc = inner_rect.create_gc(foreground=1, background=0)
        inner_rect.fill_rectangle(gc, 0, 0, w - (lw * 2), h - (lw * 2))
        gc.free()

        # First add the outer rectangle within the window at x y coordinates
        self.window.shape_mask(shape.SO.Set, shape.SK.Bounding, x, y, outer_rect)

        # Now subtract the inner rectangle at the same coordinates + line width from the outer rect
        # This creates a red rectangular outline that can be clicked through
        self.window.shape_mask(shape.SO.Subtract, shape.SK.Bounding, x + lw, y + lw, inner_rect)
        self.window.shape_select_input(0)
        self.window.map()

        # use the python-ewmh lib to set extended attributes on the window. Make sure to do this after
        # calling window.map() otherwise your attributes will not be received by the window.
        self.ewmh = EWMH(display, self.screen.root)
        # Always on top
        self.ewmh.setWmState(self.window, 1, '_NET_WM_STATE_ABOVE')
        # Draw even over the task bar
        self.ewmh.setWmState(self.window, 1, '_NET_WM_STATE_FULLSCREEN')
        # Don't show the icon in the task bar
        self.ewmh.setWmState(self.window, 1, '_NET_WM_STATE_SKIP_TASKBAR')

        # Apply changes
        display.flush()

        self._destroyed = False

    # cx, cy cursor pos
    def updatePos(self, cx, cy):
        newX = cx - self.w // 2
        newY = cy - self.h // 2

        self.window.configure(x=newX, y=newY, stack_mode=X.Above)
        self.d.flush()

    def destroy(self):
        if not self._destroyed:
            try:
                self.window.destroy()
                self.d.flush()
            except:
                pass
            self._destroyed = True

    def __del__(self):
        if not self._destroyed:
            self.destroy()

def createOutlineWindow(w, h):
    instance = OutlineWindow(display.Display(), 0, 0, w, h)
    return instance
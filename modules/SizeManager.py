from os import path

from modules.ConfigManager import ConfigManager
from modules.KeyEvent import KeyEvent

class SizeManager():
    def __init__(self) -> None:
        self.config = ConfigManager()

        self.ratio = self.config.get("ratio", 1.2)
        self.w = self.config.get("init_width", 900)
        self.step = 10
        self.rstep = .1

        self.updateHeight()

    def updateHeight(self):
        self.h = int(self.w // self.ratio)

    def updateWidth(self, sign=-1, step=0):
        if step == 0:
            step = self.step

        self.w += (sign * step)
        self.updateHeight()
        self.config.update("init_width", self.w)

    def shrink(self, step=0):
        self.updateWidth(-1, step)

    def expand(self, step=0):
        self.updateWidth(1, step)
    

    def updateRatio(self):
        self.ratio = max(0.2, self.ratio)
        self.ratio = min(4, self.ratio)

        self.updateHeight()
        self.config.update("ratio", self.ratio)

    def shrinkRatio(self):
        self.ratio -= self.rstep
        self.updateRatio()

    def expandRatio(self):
        self.ratio += self.rstep
        self.updateRatio()

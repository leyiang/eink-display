from os import path

class SizeManager():
    def __init__(self, ratio=1, init_width=1000) -> None:
        self.ratio = ratio
        self.step = 10
        self.w = init_width
        self.updateHeight()

    def updateHeight(self):
        self.h = int(self.w // self.ratio)

    def updateWidth(self, sign=-1, step=0):
        if step == 0:
            step = self.step

        self.w += (sign * step)
        self.updateHeight()

        basepath = path.dirname(__file__)
        filepath = path.abspath(path.join(basepath, "..", "config", "init_width"))

        with open(filepath, "w") as file:
            file.write( str(self.w) )
            file.close()

    def shrink(self, step=0):
        self.updateWidth(-1, step)

    def expand(self, step=0):
        self.updateWidth(1, step)
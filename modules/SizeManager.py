class SizeManager():
    def __init__(self, ratio=1, init_width=1000) -> None:
        self.ratio = ratio
        self.w = init_width
        self.h = self.w / self.ratio

from os import path
import toml

class ConfigManager():
    def __init__(self) -> None:
        basepath = path.dirname(__file__)
        filepath = path.abspath(path.join(basepath, "..", "config.toml"))

        with open( filepath, "r" ) as file:
            raw = file.read()
            self.config = toml.loads( raw )

    def get(self, key, defaultValue):
        if key in self.config:
            return self.config[key]
        else:
            return defaultValue
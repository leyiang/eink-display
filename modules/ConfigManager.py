from os import path
import toml

class ConfigManager():
    def __init__(self) -> None:
        basepath = path.dirname(__file__)
        self.filepath = filepath = path.abspath(path.join(basepath, "..", "config.toml"))

        with open(filepath, "r") as file:
            raw = file.read()
            self.config = toml.loads( raw )
            file.close()

    def get(self, key, defaultValue):
        if key in self.config:
            return self.config[key]
        else:
            return defaultValue

    def update(self, key, val):
        if key not in self.config: return
        self.config[key] = val
        self.saveConfig()

    def saveConfig(self):
        output = toml.dumps(self.config)
        with open(self.filepath, "w") as file:
            file.write( output )


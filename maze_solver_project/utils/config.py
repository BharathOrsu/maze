import yaml

class Config:
    def __init__(self, config_file="config.yaml"):
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        self.config = config

    def get(self, key):
        return self.config.get(key)

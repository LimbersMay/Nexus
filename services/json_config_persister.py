from models.app_config import ZoneConfig, RootConfig


class JsonConfigPersister:
    def __init__(self, json_path, root_config: RootConfig):
        self.json_file_path = json_path
        self.root_config = root_config

    def save(self):
        with open(self.json_file_path, 'w', encoding='utf-8') as json_file:
            json_file.write(self.root_config.model_dump_json(indent=4, by_alias=True))

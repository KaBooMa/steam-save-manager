from dataclasses import asdict, dataclass, fields, field
import json, os
from typing import List

PERSISTENT_DATA_FILE = 'persist.json'

@dataclass
class PersistentData:
    selected_app_id: str = None
    active_save: str = None
    app_active_saves: dict = field(default_factory=dict)
    save_metadata: dict[dict[dict]] = field(default_factory=dict)
    _initialized: bool = False


    def __post_init__(self):
        self.load()
        self.__initialized = True


    def load(self):
        if not os.path.exists(PERSISTENT_DATA_FILE):
            return

        data = json.loads(open(PERSISTENT_DATA_FILE).read())
        for key, value in data.items():
            setattr(self, key, value)


    def save(self):
        if not self.__initialized:
            return
        
        data_dict = {field.name:getattr(self, field.name) for field in fields(self) if not field.name.startswith('_')}
        data_json = json.dumps(data_dict)
        open(PERSISTENT_DATA_FILE, 'w').write(data_json)
from dataclasses import dataclass, field
import json


@dataclass
class Localization:
    filepath: str
    data: dict = None

    def __post_init__(self):
        self.load()

    def load(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except OSError:
            print(f"{self.filepath} not found!")

    def get(self, key: str) -> str:
        return self.data.get(key)

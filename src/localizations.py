from dataclasses import dataclass
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

    def __getattr__(self, item: str) -> str:
        if item not in self.data:
            print(f"ERROR! {item} not found in localization!")
        return self.get(item)

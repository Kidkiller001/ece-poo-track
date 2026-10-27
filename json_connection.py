
import json
from pathlib import Path


class JsonConnection:
    def __init__(self, file_path="data/festival.json"):
        project_dir = Path(__file__).resolve().parent
        self.file_path = project_dir / file_path
        self._data = self._load_data()

    def _load_data(self):
        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @property
    def data(self):
        return self._data

    @property
    def venues(self):
        return self._data["venues"]

    @property
    def performances(self):
        return self._data["performances"]

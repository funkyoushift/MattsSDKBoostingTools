"""Host-local lifetime joins. No guest names, IDs, or item codes are persisted."""
import json
import os
from pathlib import Path


class JoinStats:
    def __init__(self, path=None):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        self.path = Path(path) if path else Path(base) / "MattsSDKBoostingTools" / "afk_join_stats.json"

    def load(self):
        if not self.path.exists():
            return 0
        value = json.loads(self.path.read_text(encoding="utf-8"))["lifetime_joins"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Lifetime join count is invalid; original file preserved.")
        return value

    def save(self, count):
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("Invalid lifetime join count")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as stream:
            json.dump({"version": 1, "lifetime_joins": count}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.path)

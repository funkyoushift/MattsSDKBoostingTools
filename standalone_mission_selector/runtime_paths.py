from pathlib import Path
from mods_base import SETTINGS_DIR as SDK_SETTINGS_DIR

# Keep standalone replay state separate from MSBT.
SETTINGS_DIR = Path(SDK_SETTINGS_DIR) / "BL4MissionSelector" / "native"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

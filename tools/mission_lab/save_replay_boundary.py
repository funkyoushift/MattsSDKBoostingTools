"""Compatibility entry point for the packaged, pure replay editor."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / 'external_app/v22_parts_codes_fixed'))
from mission_save_boundary import *  # noqa: F403

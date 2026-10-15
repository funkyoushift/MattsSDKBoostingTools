"""Load the real build resolver for legacy isolated-file mission fixtures."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def exec_with_profiles(spec, module, monkeypatch):
    previous = module.__package__
    if not previous:
        name = '_msbt_mission_profile_fixture'
        package = ModuleType(name)
        package.__path__ = [str(Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools')]
        monkeypatch.setitem(sys.modules, name, package)
        module.__package__ = name
    spec.loader.exec_module(module)
    module.__package__ = previous

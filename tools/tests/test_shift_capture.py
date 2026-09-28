import importlib.util
from pathlib import Path


def test_close_never_reinstates_capture_exclusion(monkeypatch):
    path = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/shift_capture.py'
    spec = importlib.util.spec_from_file_location('capture_test', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    class Api:
        affinity = 17
        writes = []
        def EnumWindows(self, visit, arg): visit(123, arg)
        def GetWindowThreadProcessId(self, hwnd, out): out._obj.value = mod.os.getpid()
        def GetClassNameW(self, hwnd, out, size): out.value = 'UnrealWindow'
        def GetWindowDisplayAffinity(self, hwnd, out): out._obj.value = self.affinity; return True
        def SetWindowDisplayAffinity(self, hwnd, value): self.writes.append(value); self.affinity = value; return True
    api = Api()
    monkeypatch.setattr(mod, '_api', lambda: (api, lambda fn: fn))
    assert mod.enable()['capture_affinity'] == 0
    api.affinity = 1  # Native close reapplies black-window protection.
    assert mod.restore()['capture_affinity'] == 0
    api.affinity = 17  # A later native transition must also be repaired.
    assert mod.enable()['capture_affinity'] == 0
    assert api.writes == [0, 0, 0]

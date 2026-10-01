import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

PATH = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/guest_inventory.py'
spec = importlib.util.spec_from_file_location('guest_inventory_test', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def pc(addr=1, role=2):
    return SimpleNamespace(_get_address=lambda:addr, Role=role, PlayerState=object(), Pawn=object())

def test_only_loaded_local_guest(monkeypatch):
    local = pc()
    monkeypatch.setitem(sys.modules, 'mods_base', SimpleNamespace(get_pc=lambda:local))
    m.require_local_guest(pc())
    for target in [None, pc(2), pc(role=3)]:
        with pytest.raises(RuntimeError): m.require_local_guest(target)
    local.Pawn = None
    with pytest.raises(RuntimeError): m.require_local_guest(local)

def test_unknown_guest_build_fails_before_binding():
    with pytest.raises(RuntimeError): m.GuestInventory(SimpleNamespace(profile='unknown'))

def test_drop_validates_entire_snapshot_before_submitting(monkeypatch):
    local=pc()
    monkeypatch.setitem(sys.modules, 'mods_base', SimpleNamespace(get_pc=lambda:local))
    def row(handle, slot=-1, quantity=1):
        return SimpleNamespace(InventoryItem=SimpleNamespace(Handle=SimpleNamespace(Handle=handle), EquipSlot=slot, item=SimpleNamespace(State=SimpleNamespace(Quantity=quantity))))
    local.PlayerState=SimpleNamespace(BackpackItems=SimpleNamespace(items=[row(1),row(2),row(3,0)]))
    instance=object.__new__(m.GuestInventory)
    calls=[]
    instance.transaction=lambda pc,handle,send=True:calls.append((handle,send))
    instance.drop_backpack(local)
    assert calls==[(1,False),(2,False),(1,True),(2,True)]
    calls.clear()
    local.PlayerState.BackpackItems.items.append(row(4,quantity=2))
    with pytest.raises(RuntimeError): instance.drop_backpack(local)
    assert calls==[]


def test_complete_profile_required(monkeypatch):
    for profile in ('steam-25372571', 'epic-4845623'):
        gates=((10,3,__import__('hashlib').sha256(b'abc').hexdigest()),)
        monkeypatch.setitem(m.PROFILES,profile,gates)
        engine=SimpleNamespace(profile=profile,base=100,read=lambda addr,size:b'abc' if addr==110 and size==3 else b'bad')
        assert m.select_gates(engine)==gates
        engine.read=lambda addr,size:b'bad'
        with pytest.raises(RuntimeError):m.select_gates(engine)

"""Compare production request bytes with the preserved live-success trial.

All allocations and calls are test doubles; this never accesses the game.
"""
import ctypes as C
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

production = load('guest_transaction_production', ROOT/'mod_extracted/MattsSDKBoostingTools/guest_inventory.py')
reference = load('guest_transaction_reference', Path(__file__).parent/'fixtures/guest_transaction_sept30.py')

@pytest.mark.parametrize('handle', [1199, -2, None])
@pytest.mark.parametrize('send', [True, False])
def test_production_preserves_successful_trial_request_bytes(monkeypatch, handle, send):
    pc = SimpleNamespace(Role=2, _get_address=lambda:0x10000, PlayerState=object(), Pawn=object(),
        ExecuteInventoryTransactionOnServer=SimpleNamespace(func=SimpleNamespace(_get_address=lambda:0x20000)),
        StructuredInteractableUserState=SimpleNamespace(ClientSetCurrentInteractable=SimpleNamespace(func='name')))
    monkeypatch.setitem(sys.modules, 'mods_base', SimpleNamespace(get_pc=lambda:pc))
    identity = C.create_string_buffer(bytes(range(216)))
    identity_address = C.addressof(identity) if handle is None else None

    def run(legacy):
        storage, name_storage = C.create_string_buffer(376), C.create_string_buffer(8)
        address, name_address = C.addressof(storage), C.addressof(name_storage)
        assert address % 16 == 0
        C.c_uint64.from_address(name_address).value = 0x123456
        snapshots, submissions, cleanup = [], [], []
        class Transaction:
            def _get_address(self): return address
            def __setattr__(self, key, value):
                offset = {'SourceContainerOwner':0x10, 'TargetContainerOwner':0x20}[key]
                C.c_uint64.from_address(address+offset).value = value._get_address()
                C.c_uint64.from_address(address+offset+8).value = value._get_address()+8
        def wrapped(function, **kwargs):
            if function == 'name':
                assert kwargs == {'InteractionName':'Backpack'}
                return SimpleNamespace(_get_address=lambda:name_address,
                    _type=SimpleNamespace(_find_prop=lambda _:SimpleNamespace(ElementSize=8,Offset_Internal=0)))
            return SimpleNamespace(Transaction=Transaction())
        def validate(addr):
            snapshots.append(C.string_at(addr,376))
            return True
        callbacks = dict(initialize=lambda addr:C.memset(addr,0,376),
            copy_identity=lambda dest,src:C.memmove(dest,src,216),
            destroy=lambda owner,addr:cleanup.append(C.string_at(addr,376)),
            validate=validate,invoke=lambda owner,func,addr:submissions.append((owner,func,C.string_at(addr,376))))
        if legacy:
            for key,value in dict(C=C,WrappedStruct=wrapped,**callbacks).items(): monkeypatch.setattr(reference,key,value,raising=False)
            reference.transaction(pc,identity_address=identity_address,handle=handle,send=send)
        else:
            monkeypatch.setitem(sys.modules,'unrealsdk.unreal',SimpleNamespace(WrappedStruct=wrapped))
            instance=object.__new__(production.GuestInventory)
            for key,value in callbacks.items():setattr(instance,key,value)
            instance.transaction(pc,identity_address=identity_address,handle=handle,send=send)
        assert len(cleanup)==1 and C.string_at(address,376)==bytes(376)
        assert len(submissions)==int(send)
        return snapshots,submissions,cleanup
    assert run(False)==run(True)

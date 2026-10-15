"""Request the clients' real entitlement snapshots before bulk progression.

Observe the normal server RPC after it returns. Never construct an entitlement
snapshot, grant access, or infer ownership from shared mission/world progress.
"""
import time
import uuid
import unrealsdk
from unrealsdk.hooks import Type

HOOK='/Script/GbxGame.GbxPlayerController:ServerRefreshPlayerEntitlementFacts'
_state=None


def identity(row):
    pc=row['pc']
    if pc is None or pc.PlayerState is None or not pc.HasAuthority():
        raise RuntimeError('DLC refresh player is unavailable')
    if pc.PlayerState._get_address()!=row['state']._get_address():
        raise RuntimeError('DLC refresh player identity changed')
    return (pc._get_address(),pc._path_name(),row['state']._get_address())


def begin(rows):
    global _state
    if _state is not None:raise RuntimeError('An entitlement refresh already needs inspection')
    targets=[r for r in rows if not r['host']]
    expected=[identity(r) for r in targets]
    token=uuid.uuid4().hex
    state=dict(id=token,expected=expected,ack=set(),deadline=time.monotonic()+15,hook='MSBT_DLC_'+token)
    _state=state
    if not targets:return dict(kind='access_refresh',id=token)
    def observed(pc,_args,_ret,_func):
        if _state is not state:return
        try:
            key=(pc._get_address(),pc._path_name(),pc.PlayerState._get_address())
            if key in state['expected']:state['ack'].add(key)
        except Exception:
            pass
    try:
        unrealsdk.hooks.add_hook(HOOK,Type.POST,state['hook'],observed)
        for row in targets:
            row['pc'].Client_RequestDLCEntitlements()
    except Exception:
        cancel(token)
        raise
    return dict(kind='access_refresh',id=token)


def ready(token,rows):
    state=_state
    if not state or state['id']!=token:raise RuntimeError('Original entitlement refresh is unavailable; no request repeated')
    current=[identity(r) for r in rows if not r['host']]
    if current!=state['expected']:raise RuntimeError('DLC refresh lobby changed; no player substituted')
    if set(current)<=state['ack']:
        cancel(token)
        return True
    if time.monotonic()>=state['deadline']:
        raise RuntimeError('Visitor entitlement refresh was not confirmed; no missions sent')
    return False


def cancel(token):
    global _state
    if _state and _state['id']==token:
        state=_state
        if state['expected']:unrealsdk.hooks.remove_hook(HOOK,Type.POST,state['hook'])
        _state=None

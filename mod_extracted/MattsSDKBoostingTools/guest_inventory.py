"""Steam build-gated local guest transactions. Game thread only.

See docs/GUEST_INVENTORY.md for native evidence and live-test limitations.
"""
import ctypes as C
import hashlib

GATES = ((92278004, 176, '98ec6a79a0eabb62f952b91f47c672e801d906572f36766c0d47d0cbeba6bc93'), (7338990, 471, '890ee1006dbac9c4c00650bcd710c0bc2375d8655f609b3c7a17b6972b594408'), (3579156, 184, '69745be40196a35f3df4aa98c5f0453fbd12018fd71925dc5fe0d3d76a91c559'), (105779922, 44, '4e18b428c6dac3e7ba066a17f34aa9ebb6f6b55fe8bca64c978b256ad0bd84b2'), (98605076, 909, '30918358a19d83e8540acdfc9833ae61664a37685ae10af5e1ed6b3f86bdffcd'), (19828340, 22, '44645cf9f58a57466dd40e044c9d7044acee0700bc6ca3bc23d60b53fda8f66f'), (98177860, 47, 'd9d28effaf83f7b697c30ce4f029ad8b29d5d6b5cdb17535454834df5cb2c312'), (98177908, 64, 'f2d727276ed9af34aa3b79a7c2fd1c1f5b1ea0329f65ffefcc5573befbb15093'), (98605076, 909, '30918358a19d83e8540acdfc9833ae61664a37685ae10af5e1ed6b3f86bdffcd'), (64708632, 395, '2a4cf3c9cdb141a9589c1a57d4230528140086d5397d52726962fcaaaf5aa1b6'), (102962020, 2095, 'b7d2faf3b2c1ec10e2867021598cee3c327bc23072d5f1805c95c64f27893908'))


def require_local_guest(pc):
    from mods_base import get_pc
    local = get_pc()
    if (local is None or pc is None or int(local.Role) != 2
            or int(pc.Role) != 2 or pc._get_address() != local._get_address()
            or pc.PlayerState is None or pc.Pawn is None):
        raise RuntimeError('Guest inventory actions can only target your own loaded character.')


class GuestInventory:
    def __init__(self, engine):
        if engine.profile != 'steam-25372571':
            raise RuntimeError('Guest inventory actions are not supported on this game build.')
        for rva, size, digest in GATES:
            if hashlib.sha256(engine.read(engine.base + rva, size)).hexdigest() != digest:
                raise RuntimeError('Guest inventory native code changed; no request sent.')
        self.initialize = C.CFUNCTYPE(C.c_void_p, C.c_void_p)(engine.base + 92278004)
        self.copy_identity = C.CFUNCTYPE(C.c_void_p, C.c_void_p, C.c_void_p)(engine.base + 7338990)
        self.destroy = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p)(engine.base + 105779922)
        self.validate = C.CFUNCTYPE(C.c_bool, C.c_void_p)(engine.base + 98605076)
        # Bind the already loaded SDK, never a guessed installation path.
        kernel = C.WinDLL('kernel32', use_last_error=True)
        kernel.GetModuleHandleW.argtypes = [C.c_wchar_p]
        kernel.GetModuleHandleW.restype = C.c_void_p
        handle = kernel.GetModuleHandleW('unrealsdk.dll')
        if not handle:
            raise RuntimeError('Loaded Unreal SDK could not be resolved.')
        self.dll = C.CDLL('unrealsdk.dll', handle=handle)
        self.invoke = self.dll._unrealsdk_export__process_event
        self.invoke.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]
        self.invoke.restype = None

    def transaction(self, pc, identity_address=None, handle=None, send=True):
        from unrealsdk.unreal import WrappedStruct
        require_local_guest(pc)
        if (identity_address is None) == (handle is None):
            raise ValueError('Exactly one inventory operation is required.')
        params = WrappedStruct(pc.ExecuteInventoryTransactionOnServer.func)
        t = params.Transaction
        a = t._get_address()
        if a % 16:
            raise RuntimeError('Transaction is not aligned.')
        self.initialize(a)
        try:
            name = WrappedStruct(pc.StructuredInteractableUserState.ClientSetCurrentInteractable.func, InteractionName='Backpack')
            prop = name._type._find_prop('InteractionName')
            if prop.ElementSize != 8:
                raise RuntimeError('Container name layout changed.')
            if handle is None:
                t.TargetContainerOwner = pc
                C.memmove(a + 0x130, name._get_address() + prop.Offset_Internal, 8)
                self.copy_identity(a + 0x50, identity_address)
                C.c_uint8.from_address(a).value = 15
                C.c_uint32.from_address(a + 0x164).value = 8
                C.c_uint32.from_address(a + 0x16c).value = 1
            else:
                t.SourceContainerOwner = pc
                C.memmove(a + 0x128, name._get_address() + prop.Offset_Internal, 8)
                C.c_int32.from_address(a + 4).value = handle
                C.c_uint8.from_address(a).value = 6
                C.c_uint32.from_address(a + 0x164).value = 1
                C.c_uint32.from_address(a + 0x168).value = 1
            if not self.validate(a):
                raise RuntimeError('Native inventory transaction rejected.')
            if send:
                self.invoke(pc._get_address(), pc.ExecuteInventoryTransactionOnServer.func._get_address(), a)
        finally:
            self.destroy(None, a)
            C.memset(a, 0, 376)

    def drop_backpack(self, pc):
        require_local_guest(pc)
        rows = [row.InventoryItem for row in pc.PlayerState.BackpackItems.items
                if int(row.InventoryItem.Handle.Handle) >= 0 and int(row.InventoryItem.EquipSlot) == -1]
        if any(int(row.item.State.Quantity) != 1 for row in rows):
            raise RuntimeError('Stacked inventory has not been validated for guest drop; nothing sent.')
        handles = [int(row.Handle.Handle) for row in rows]
        if len(set(handles)) != len(handles):
            raise RuntimeError('Duplicate inventory handles; nothing sent.')
        # Validate the full snapshot before the first mutation. Never retry a submitted drop.
        for handle in handles:
            self.transaction(pc, handle=handle, send=False)
        sent = 0
        try:
            for handle in handles:
                self.transaction(pc, handle=handle)
                sent += 1
        except Exception as exc:
            raise RuntimeError(f'Drop stopped after {sent}/{len(handles)} requests; check inventory before retrying: {exc}') from exc
        return f'drop backpack OK: submitted {sent} drop requests; waiting for the host to replicate ground items.'

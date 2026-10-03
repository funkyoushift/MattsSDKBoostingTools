"""Build-gated local guest transactions. Game thread only.

See docs/GUEST_INVENTORY.md for native evidence and live-test limitations.
"""
import ctypes as C
import hashlib

GATES = ((92278004, 176, '98ec6a79a0eabb62f952b91f47c672e801d906572f36766c0d47d0cbeba6bc93'), (7338990, 471, '890ee1006dbac9c4c00650bcd710c0bc2375d8655f609b3c7a17b6972b594408'), (3579156, 184, '69745be40196a35f3df4aa98c5f0453fbd12018fd71925dc5fe0d3d76a91c559'), (105779922, 44, '4e18b428c6dac3e7ba066a17f34aa9ebb6f6b55fe8bca64c978b256ad0bd84b2'), (98605076, 909, '30918358a19d83e8540acdfc9833ae61664a37685ae10af5e1ed6b3f86bdffcd'), (19828340, 22, '44645cf9f58a57466dd40e044c9d7044acee0700bc6ca3bc23d60b53fda8f66f'), (98177860, 47, 'd9d28effaf83f7b697c30ce4f029ad8b29d5d6b5cdb17535454834df5cb2c312'), (98177908, 64, 'f2d727276ed9af34aa3b79a7c2fd1c1f5b1ea0329f65ffefcc5573befbb15093'), (98605076, 909, '30918358a19d83e8540acdfc9833ae61664a37685ae10af5e1ed6b3f86bdffcd'), (64708632, 395, '2a4cf3c9cdb141a9589c1a57d4230528140086d5397d52726962fcaaaf5aa1b6'), (102962020, 2095, 'b7d2faf3b2c1ec10e2867021598cee3c327bc23072d5f1805c95c64f27893908'))

GATES += ((22482466, 660, 'aee463accbfa8d978e190333d37d48c7a5fae1297f538a24c19a98cc9846a15f'), (103125735, 765, '1abd5696eeae574c00758b67c0902acc147329f4fa494bd4a250982d47d2eba0'))
EPIC_GATES = ((92347916, 176, '9551f8a5aa55dc10eee3505eacbae3d921be88f93923f2c8fb2c4c8e8eeaa188'), (7338990, 471, 'bcd7af3bd5339f1d21b990ad37311aa4a35de01d5e212262ad086c3111e0f1ef'), (3579156, 184, '69745be40196a35f3df4aa98c5f0453fbd12018fd71925dc5fe0d3d76a91c559'), (105813370, 44, '873fa825bd9d555163b6f1101241048ad3a0c50986472154c18d163d80a0b3b9'), (98656758, 909, '71c3ebcdefeb99474b35030044e7d04b401bccf14991fe530a21152b72912a5e'), (19818562, 22, '44645cf9f58a57466dd40e044c9d7044acee0700bc6ca3bc23d60b53fda8f66f'), (98231710, 47, '79786c3ecc132798e65f6b95c2023afef3c5094aa885b742da56a85aa2304bc9'), (98231758, 64, '4d8018284a0a55500844d99980a214b55af435208ab41795338607aa8d74f4b9'), (98656758, 909, '71c3ebcdefeb99474b35030044e7d04b401bccf14991fe530a21152b72912a5e'), (64665264, 395, '8088f12190c8c29359d42585532a33c3e786286730b82ea43dc4081d74bd3ef3'), (102996038, 2095, '11d8e3cfe7ad11091770dadf664509181ebd62a897650248f6daf1d41aa4d2e2'), (22465850, 660, 'e8cfa1683db732ead66b76c47d30dab2281c719c6568950a1c064fd958f4c64f'), (103159737, 765, '87ce3a042491a6182a3f66133fc6df02d233d67fed687df835e99527e79e5a12'))
PROFILES = {'steam-25372571': GATES, 'epic-4845623': EPIC_GATES}


def select_gates(engine):
    gates = PROFILES.get(engine.profile)
    if gates is None:
        raise RuntimeError('Guest inventory actions are not supported on this game build.')
    for rva, size, digest in gates:
        if hashlib.sha256(engine.read(engine.base + rva, size)).hexdigest() != digest:
            raise RuntimeError('Guest inventory native code changed; no request sent.')
    return gates


def require_local_guest(pc):
    from mods_base import get_pc
    local = get_pc()
    if (local is None or pc is None or int(local.Role) != 2
            or int(pc.Role) != 2 or pc._get_address() != local._get_address()
            or pc.PlayerState is None or pc.Pawn is None):
        raise RuntimeError('Guest inventory actions can only target your own loaded character.')


def backpack_diagnostics(pc):
    """Read local row metadata without binding native functions or submitting RPCs."""
    result = {'role': int(pc.Role), 'rows': [], 'row_errors': [], 'eligible_count': 0, 'total_rows': 0, 'error_count': 0}
    for index, source in enumerate(pc.PlayerState.BackpackItems.items):
        result["total_rows"] += 1
        try:
            item = source.InventoryItem
            handle, slot = int(item.Handle.Handle), int(item.EquipSlot)
            quantity = int(item.item.State.Quantity)
            if len(result['rows']) < 64:
                result['rows'].append({'index': index, 'handle': handle, 'equip_slot': slot, 'quantity': quantity})
            result['eligible_count'] += int(handle != -1 and slot == -1)
        except Exception as exc:
            result['error_count'] += 1
            if len(result['row_errors']) < 8:
                result['row_errors'].append({'index': index, 'error': str(exc)})
    return result


class GuestInventory:
    def __init__(self, engine):
        gates = select_gates(engine)
        initialize, copy_identity, _identity_cleanup, destroy, validate = (g[0] for g in gates[:5])
        self.initialize = C.CFUNCTYPE(C.c_void_p, C.c_void_p)(engine.base + initialize)
        self.copy_identity = C.CFUNCTYPE(C.c_void_p, C.c_void_p, C.c_void_p)(engine.base + copy_identity)
        self.destroy = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p)(engine.base + destroy)
        self.validate = C.CFUNCTYPE(C.c_bool, C.c_void_p)(engine.base + validate)
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
        # Native operation 6 validates Handle != -1, not Handle >= 0.
        # Steam 25372571: switch 0xb40b8f8, branch 0x5e098d4.
        rows = [row.InventoryItem for row in pc.PlayerState.BackpackItems.items
                if int(row.InventoryItem.Handle.Handle) != -1 and int(row.InventoryItem.EquipSlot) == -1]
        if any(int(row.item.State.Quantity) != 1 for row in rows):
            raise RuntimeError('Stacked inventory has not been validated for guest drop; nothing sent.')
        handles = [int(row.Handle.Handle) for row in rows]
        if not handles:
            raise RuntimeError(f'No eligible backpack items; no drop requests sent. Local snapshot: {backpack_diagnostics(pc)}')
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

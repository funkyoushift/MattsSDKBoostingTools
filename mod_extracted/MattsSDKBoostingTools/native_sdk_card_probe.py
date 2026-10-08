"""Opt-in research probe, invoked on the SDK game thread, never on import.

Steam 25372571 and Epic 4845623 candidate. Creates detached item/model storage, calls the recovered
native builder, exports strings, then destroys native allocations. It never
calls inventory insertion. See NATIVE_UI_ROW_PROJECTION.md for source receipts.
Not a public API or a background-thread-safe renderer.
"""
import ctypes as C
import hashlib
import json
import struct
import time
from pathlib import Path

from .native_card_model_read import read_model, read_ui_rows
from .native_card_builds import STEAM, card_rva, card_gates, require_card_profile

GATES = (
    (0x56D3CCA, 0x56D3FCE, '5ce1aaa8933709a337c65faf40db6c17e45ec6bbc895296c8fc71b30d1a58802'),
    (0xBABBE2, 0xBABC51, 'd69c483030211fa666465e66e55105f947ce61c406b5497d78f604528ecc5e70'),
    (0xBAC7D2, 0xBACE63, '6aff5e04e3b4d3bb0ebbf2aafe5c21dc5f0150771b3b4b6bc7c07297527e5319'),
    (0xBAF88E, 0xBB097B, '51bd17ddef73d78301659fe08778d375c51dff57bdfb7cab293a941f66a6a4d5'),
    (0x8E1AA38, 0x8E1AA5E, 'fe7689fda843ad3179819bd789dc53c22f0d1778ea6ddfba9c14dbba199dc1d8'),
    (0xE69A30, 0xE69CA9, 'ec1f59a0363723667b0d3f99537cafe84f166171ea923ed07e46dabc86e0b593'),
    (0xE69D1A, 0xE6A157, '0a8a22ae8ab912bc37dd763440fd0322b20a12884fd804f3765f4a844c971c73'),
    (0xE69CA9, 0xE69D1A, 'bfc0da2a7661a8f5f785a94a6f2ae2d54d5c0d89333506ac802a7b79a0fa67ed'),
    (0x20A8, 0x20E8, '7b0652ce5487ac59d2d731b69715d6a77a54ebcf2bcd221ea82f7ed66108978f'),
)
PRICE_GATES = (
    (0x5C4B4F8,0x5C4B50E,'ec1033a2760eeb536c16690b3e953b4cc1d1341147dd7e73d9aafacc9285e586'),
    (0x5C4B50E,0x5C4B684,'96c18b1dbda7900d1eb51cb989eeca169f923f1c7d842f676c7e4087abe770c9'),
    (0x236036,0x23614C,'471951c9b998dd98fe1120f420c18a7487e8167cf34972a3c32b3b42a881f9d1'),
    (0x479623A,0x47962B0,'0be1c20f5860b44ee8f6a96a66ece5716e2bb0c28e58c4b0e626034c7414cc34'),
    (0x4994E1A,0x4994EE7,'92b6a793b98a730f39f4f464a6dcdc17d4d1fa44f68a902b7b5ba9d4f938e1ec'),
    (0x4774916,0x4774A96,'f83496dc177e13c3d75b5b865591823d356ed2c4a9bde6fc21b04ae21cc84446'),
)
EMPTY_COMPARISON_GATES = (
    (0xB95EC6,0xB95F28,'8d005584492b7e689def0e1a72e0834ab0e6474d4e347bd6774c757de08dfadf'),
    (0xB95F28,0xB95FE1,'e7fde244391f8a884916c7c4a6b8f53b399540e14a0c47cedfd00bfc0135bd91'),
)


def fill_default_price(native, identity, model, stage):
    """Default-card price path, with owned FText and its recovered release.

    C67F12 keeps the initialized container at identity+90; it has already
    been constructed by the self-comparison fill. This function does not
    acquire another shared reference or reconstruct the stat container.
    """
    container=native.u64(identity+0x90)
    if not container or native.read(container+0x1f8,1)!=b'\x01':
        raise RuntimeError('Native price container is not initialized')
    price=struct.unpack('<I',native.read(container+0x40,4))[0]
    address=lambda rva:native.base+card_rva(native.profile,rva)
    format_price=C.CFUNCTYPE(C.c_void_p,C.c_void_p,C.c_uint32,C.c_void_p,C.c_void_p)(address(0x5C4B4F8))
    to_string=C.CFUNCTYPE(C.c_void_p,C.c_void_p)(address(0x479623A))
    copy_string=C.CFUNCTYPE(None,C.c_void_p,C.c_void_p)(address(0x4994E1A))
    release=C.CFUNCTYPE(None,C.c_void_p)(address(0x4774916))
    text=C.create_string_buffer(16)
    culture=C.create_string_buffer(16)
    pointer=0
    stage('price_format_begin')
    try:
        format_price(C.addressof(text),price,None,C.addressof(culture))
        pointer=native.u64(C.addressof(text))
        if not pointer or native.u64(pointer)!=address(0x9E12790):
            raise RuntimeError('Unexpected native formatted-text ownership')
        string=to_string(C.addressof(text))
        if not string:
            raise RuntimeError('Native formatted price has no string')
        copy_string(model+0x4b0,string)
        stage('price_copy_complete')
    finally:
        if pointer and native.u64(pointer)==address(0x9E12790):
            release(pointer)
            stage('price_text_release_complete')
    if native.read(C.addressof(culture),16)!=bytes(16):
        raise RuntimeError('Unexpected ownership in native culture argument')
    return price


def run(serial, output, *, expected_game_thread, include_price=False, include_widget=False, compare_self=True, export_model=True):
    from MattsSDKBoostingTools.direct_inventory import NativeInventory, FString
    from MattsSDKBoostingTools.party_helpers import _gbc_session_world_and_gamestate
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentThreadId.restype = C.c_ulong
    actual_thread = kernel.GetCurrentThreadId()
    if not expected_game_thread or actual_thread != expected_game_thread:
        raise RuntimeError('Must execute on the independently observed SDK game thread')
    _, game_state = _gbc_session_world_and_gamestate()
    player_count = len(game_state.PlayerArray) if game_state is not None else 0
    if player_count < 1:
        raise RuntimeError('New game cards require an active game session')
    if not isinstance(serial, str) or not serial.startswith('@U') or not serial.isascii() or len(serial) > 8192:
        raise ValueError('Unsupported probe serial')
    output = Path(output) if output is not None else None
    if output is not None and output.exists():
        raise FileExistsError('Use a new evidence filename')
    native = NativeInventory()
    require_card_profile(native.profile)
    if native.profile != STEAM and export_model:
        raise RuntimeError('Epic research model export is not verified; use the widget preview')
    if include_widget:include_price=True
    active_gates=GATES+(PRICE_GATES if include_price else ())
    if not compare_self:active_gates+=EMPTY_COMPARISON_GATES
    if include_widget:
        from .native_sdk_widget_probe import WIDGET_GATES,project_default_widget
        active_gates+=WIDGET_GATES
    active_gates=card_gates(native.profile,active_gates)
    for start, end, digest in active_gates:
        if hashlib.sha256(native.read(native.base + start, end - start)).hexdigest() != digest:
            raise RuntimeError(f'Native card function changed: {start:x}')
    bind = lambda rva, *args: C.CFUNCTYPE(None, *args)(native.base + card_rva(native.profile,rva))
    model_ctor = bind(0x56D3CCA, C.c_void_p)
    model_bind = bind(0xBABBE2, C.c_void_p, C.c_void_p, C.c_uint8)
    model_fill = bind(0xBAF88E, C.c_void_p, C.c_void_p, C.c_uint8)
    model_destroy = bind(0x8E1AA38, C.c_void_p, C.c_uint32)
    ui_convert = bind(0xE69A30, C.c_void_p, C.c_void_p)
    single_convert = bind(0xE69D1A, C.c_void_p, C.c_void_p)
    rows_destroy = bind(0xE69CA9, C.c_void_p, C.c_int32)
    native_free = bind(0x20A8, C.c_void_p)

    report = dict(profile=native.profile, thread=actual_thread, serial=serial,
                  session_players=player_count,
                  function_hashes=[dict(rva=hex(a), sha256=h) for a, _, h in active_gates],
                  stages=[], inventory_insertions=0, comparison='self' if compare_self else 'empty',
                  limitation='Single detached live SDK research probe; not complete UI binding or general safety proof')
    started = time.perf_counter()
    def stage(name):
        report['stages'].append(name)
        report['elapsed_ms'] = (time.perf_counter() - started) * 1000
        if output is None:return
        try:
            output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        except OSError as error:
            # A receipt write failure must never prevent native destruction.
            report.setdefault('journal_errors', []).append(repr(error))

    identity_storage = C.create_string_buffer(0xD8)
    comparison_storage = C.create_string_buffer(0xD8)
    model_storage = C.create_string_buffer(0x710)
    identity, model = C.addressof(identity_storage), C.addressof(model_storage)
    comparison = C.addressof(comparison_storage)
    comparison_ready = False
    if identity % 16 or model % 16 or comparison % 16:
        raise RuntimeError('Native storage alignment differs')
    C.memmove(model + 0x700, b'MSBT-card-guard!', 16)
    C.memmove(identity + 0x68, bytes.fromhex('0000000080000000ffffffff00000000'), 16)
    C.c_uint64.from_address(identity + 0xB8).value = 15
    C.c_uint16.from_address(identity + 0xC0).value = 1
    text = C.create_unicode_buffer(serial)
    value = FString(C.addressof(text), len(serial) + 1, len(serial) + 1)
    model_ready = False
    stage('gates_passed')
    try:
        stage('construct_identity_begin')
        if not native.construct(identity, C.byref(value)):
            raise RuntimeError('Native serial construction failed')
        length, capacity = native.u64(identity + 0xB0), native.u64(identity + 0xB8)
        if length != len(serial):
            raise RuntimeError('Native serial length changed')
        serial_pointer = identity + 0xA0 if capacity <= 15 else native.u64(identity + 0xA0)
        if native.read(serial_pointer, length).decode('ascii') != serial:
            raise RuntimeError('Native serial changed')
        stage('construct_model_begin')
        model_ctor(model)
        model_ready = True
        stage('bind_model_begin')
        model_bind(model, identity, 0)
        stage('fill_model_begin')
        if not compare_self:
            C.memmove(comparison+0x68, bytes.fromhex('0000000080000000ffffffff00000000'), 16)
            C.c_uint64.from_address(comparison+0xB8).value=15
            C.c_uint16.from_address(comparison+0xC0).value=1
            comparison_ready=True
            bind(0xB95EC6,C.c_void_p)(comparison)
            stage('empty_comparison_initialized')
        model_fill(model, identity if compare_self else comparison, 0)
        if include_price:
            report['monetary_value_uint32']=fill_default_price(native,identity,model,stage)
        stage('export_model_begin')
        def project_array(source):
            storage = C.create_string_buffer(24)
            at = C.addressof(storage)
            converted = False
            try:
                ui_convert(at, source)
                converted = True
                return read_ui_rows(at, native.read)
            finally:
                if converted:
                    pointer, count, capacity = struct.unpack('<Qii', native.read(at, 16))
                    if not 0 <= count <= capacity <= 8192:
                        raise RuntimeError('Cannot safely destroy invalid converted array')
                    rows_destroy(pointer, count)
                    if pointer:
                        native_free(pointer)
        def project_single(source):
            storage=C.create_string_buffer(0x70)
            at=C.addressof(storage)
            converted=False
            try:
                single_convert(at,source)
                converted=True
                array=C.create_string_buffer(struct.pack('<Qii',at,1,1))
                return read_ui_rows(C.addressof(array),native.read)[0]
            finally:
                if converted:
                    rows_destroy(at,1)  # Only inner fields; Python owns this row.
        if export_model:
            report['model_data'] = read_model(model, native.read, native.base, project_array,
                include_widget_sources=True, project_single_row=project_single)
        if include_widget:
            report['default_widget']=project_default_widget(native,model,stage)
            report['widget_context']='Initialized native owner; '+report['comparison']+' comparison; detached item; no player loadout supplied'
        if native.read(model + 0x700, 16) != b'MSBT-card-guard!':
            raise RuntimeError('Model allocation guard changed')
        stage('export_complete')
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        try:
            if model_ready:
                stage('destroy_model_begin')
                model_destroy(model, 0)  # Inner native fields only; Python owns outer storage.
                stage('destroy_model_complete')
        finally:
            try:
                if comparison_ready:
                    stage('destroy_comparison_begin')
                    native.destroy(comparison)
                    stage('destroy_comparison_complete')
            finally:
                stage('destroy_identity_begin')
                native.destroy(identity)
                stage('destroy_identity_complete')
    if report.get('journal_errors'):
        raise RuntimeError('Probe completed but could not reliably save its receipt')
    return report

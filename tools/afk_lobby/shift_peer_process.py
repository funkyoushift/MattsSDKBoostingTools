"""Read-only Windows TCP peer ownership check for the local SHiFT bridge."""
from __future__ import annotations

import ctypes
import os
import socket
import struct
import sys

_MAX_TABLE_BYTES = 16 * 1024 * 1024
_ROW = struct.Struct("<6I")  # state, local address/port, remote address/port, PID
_LOOPBACK = int.from_bytes(socket.inet_aton("127.0.0.1"), "little")


def _parse_table(data: bytes):
    if len(data) < 4 or len(data) > _MAX_TABLE_BYTES:
        raise ValueError("invalid TCP table size")
    count = struct.unpack_from("<I", data)[0]
    if count > (len(data) - 4) // _ROW.size:
        raise ValueError("invalid TCP row count")
    return [_ROW.unpack_from(data, 4 + i * _ROW.size) for i in range(count)]


def _read_rows():
    if sys.platform != "win32":
        raise OSError("Windows TCP table unavailable")
    get_table = ctypes.WinDLL("iphlpapi", use_last_error=True).GetExtendedTcpTable
    get_table.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_int,
                          ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    get_table.restype = ctypes.c_ulong
    # The TCP table can grow between the size query and the fill call. Retry
    # that documented race only; every successful snapshot still passes the
    # unchanged exact endpoint/PID checks below. Other errors fail closed.
    for _attempt in range(3):
        size = ctypes.c_ulong(0)
        if get_table(None, ctypes.byref(size), False, socket.AF_INET, 5, 0) != 122:
            raise OSError("TCP table size query failed")
        if size.value < 4 or size.value > _MAX_TABLE_BYTES:
            raise ValueError("invalid TCP table size")
        buffer = ctypes.create_string_buffer(size.value)
        result = get_table(buffer, ctypes.byref(size), False, socket.AF_INET, 5, 0)
        if result == 122:  # ERROR_INSUFFICIENT_BUFFER: query a new bounded size.
            if size.value < 4 or size.value > _MAX_TABLE_BYTES:
                raise ValueError("invalid TCP table size")
            continue
        if result != 0:
            raise OSError("TCP table query failed")
        if size.value < 4 or size.value > len(buffer):
            raise ValueError("invalid TCP table size")
        return _parse_table(buffer.raw[:size.value])
    raise OSError("TCP table changed during all read attempts")



def peer_is_game(client_address, server_port, game_pid=None):
    """Confirm the connecting loopback endpoint belongs to this game process.

    For the accepted socket, require one exact row in each direction, both
    owned by the game PID, and at least one ESTABLISHED row. Some Windows
    builds misreport one side's state. Errors and ambiguity fail closed.
    """
    try:
        if not isinstance(client_address, (tuple, list)) or len(client_address) != 2:
            return False
        host, port = client_address
        if host != "127.0.0.1" or type(port) is not int or not 1 <= port <= 65535:
            return False
        if type(server_port) is not int or not 1 <= server_port <= 65535 or port == server_port:
            return False
        pid = os.getpid() if game_pid is None else game_pid
        if type(pid) is not int or not 1 <= pid <= 0xffffffff:
            return False
        client_rows, server_rows = [], []
        for row in _read_rows():
            state, local_addr, local_port, remote_addr, remote_port, owner = row
            if local_addr != _LOOPBACK or remote_addr != _LOOPBACK:
                continue
            local = socket.ntohs(local_port & 0xffff)
            remote = socket.ntohs(remote_port & 0xffff)
            if local == port and remote == server_port:
                client_rows.append((state, owner))
            if local == server_port and remote == port:
                server_rows.append((state, owner))
        if len(client_rows) != 1 or len(server_rows) != 1:
            return False
        client_state, client_owner = client_rows[0]
        server_state, server_owner = server_rows[0]
        return client_owner == server_owner == pid and (client_state == 5 or server_state == 5)
    except Exception:
        return False

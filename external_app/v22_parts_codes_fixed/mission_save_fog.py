"""Fog-only edits to native, already-saved discovery grids.

Never creates guessed grids for unvisited maps or changes discovery metrics.
Native saves observed on 2026-10-15 use base64 Zlib byte grids. Zero is the
unrevealed value and 255 the explored value; visual in-game verification remains
separate from format/preservation validation.
"""
import base64
import binascii
import zlib

import yaml
from mission_save_boundary import BoundaryError, canonical, mapping, member, scalar_edit

MODES = ('leave', 'clear', 'restore')
MAX_GRID = 4 * 1024 * 1024


def apply(text, mode='leave'):
    if mode not in MODES:
        raise BoundaryError('Choose leave, clear or restore for map fog')
    if mode == 'leave':
        return text, dict(mode=mode, grids_changed=0)
    tree = yaml.compose(text)
    discovery = mapping(tree).get('gbx_discovery_pc')
    grids = mapping(discovery[1]).get('foddatas') if discovery else None
    if not grids or not isinstance(grids[1], yaml.SequenceNode):
        raise BoundaryError('This save has no supported saved map fog grids; leave fog unchanged instead')
    edits, expected, names = [], [], set()
    for grid in grids[1].value:
        name = member(grid, 'levelname').value
        if not name or name.casefold() in names:
            raise BoundaryError('Duplicate or missing map in saved fog grids')
        names.add(name.casefold())
        dimensions = [member(grid, field).value for field in ('foddimensionx', 'foddimensiony')]
        if any(not v.isascii() or not v.isdecimal() or len(v) > 7 for v in dimensions):
            raise BoundaryError('Invalid saved fog dimensions')
        width, height = map(int, dimensions)
        size = width * height
        if not width or not height or size > MAX_GRID:
            raise BoundaryError('Saved fog grid exceeds the supported size')
        if member(grid, 'compressiontype').value != 'Zlib':
            raise BoundaryError('Unsupported saved fog compression; no save was edited')
        data = member(grid, 'foddata')
        try:
            if len(data.value) > MAX_GRID * 2:
                raise ValueError('Oversized compressed grid')
            compressed = base64.b64decode(data.value, validate=True)
            stream = zlib.decompressobj()
            raw = stream.decompress(compressed, size + 1)
            if len(raw) != size or not stream.eof or stream.unused_data or stream.unconsumed_tail:
                raise ValueError('Fog grid length differs from its dimensions')
        except (ValueError, binascii.Error, zlib.error) as exc:
            raise BoundaryError('Saved map fog data is invalid; no save was edited') from exc
        replacement = base64.b64encode(zlib.compress(bytes([255 if mode == 'clear' else 0]) * size)).decode('ascii')
        edits.append(scalar_edit(text, data, replacement))
        expected.append((data, replacement))
    if not edits:
        raise BoundaryError('This save has no recorded map fog to change; leave fog unchanged instead')
    candidate = text
    for start, end, replacement in sorted(edits, reverse=True):
        candidate = candidate[:start] + replacement + candidate[end:]
    # Match the complete tagged save, allowing ONLY the selected foddata scalars.
    for data, replacement in expected:
        data.value = replacement
    if canonical(tree) != canonical(yaml.compose(candidate)):
        raise BoundaryError('Fog edit changed protected save data')
    return candidate, dict(mode=mode, grids_changed=len(edits), maps=sorted(names),
                           scope='existing_saved_grids', unvisited_maps_created=False)

"""Fog edits preserve every other tagged save value; no game/real-save writes."""
import base64
from pathlib import Path
import sys
import zlib

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[2] / 'external_app/v22_parts_codes_fixed'))
from mission_save_fog import apply
from mission_save_boundary import BoundaryError, canonical, member
from mission_save_replay import edit
from test_mission_selection_state import SAVE, spec


def fog_save():
    compressed = base64.b64encode(zlib.compress(bytes([0, 1, 127, 255]))).decode()
    return SAVE + f'''gbx_discovery_pc:
  metrics: !native {{seen_worlds: [World_P], untouched: 17}}
  pins_state: [retained]
  foddatas:
  - levelname: World_P
    foddimensionx: 2
    foddimensiony: 2
    compressiontype: Zlib
    foddata: !nativefog '{compressed}'
'''


def pixels(text):
    grid = member(member(yaml.compose(text), 'gbx_discovery_pc'), 'foddatas').value[0]
    return zlib.decompress(base64.b64decode(member(grid, 'foddata').value))


def test_default_is_byte_exact_even_for_unrecognized_fog_format():
    text = fog_save().replace('Zlib', 'Unknown')
    assert apply(text)[0] == text
    assert apply(SAVE)[0] == SAVE


@pytest.mark.parametrize('mode,expected', [('clear', 255), ('restore', 0)])
def test_only_grid_pixels_change_and_native_metadata_is_preserved(mode, expected):
    before = fog_save()
    after, receipt = apply(before, mode)
    assert pixels(after) == bytes([expected]) * 4
    assert receipt['grids_changed'] == 1 and not receipt['unvisited_maps_created']
    left, right = yaml.compose(before), yaml.compose(after)
    for tree in (left, right):
        grid = member(member(tree, 'gbx_discovery_pc'), 'foddatas').value[0]
        data = member(grid, 'foddata')
        assert data.tag == '!nativefog'
        data.value = 'normalized'
    assert canonical(left) == canonical(right)
    assert apply(after, mode)[0] == after


@pytest.mark.parametrize('broken', [
    lambda s: s.replace('Zlib', 'Unknown'),
    lambda s: s.replace('foddimensionx: 2', 'foddimensionx: 3'),
    lambda s: s.replace('foddimensiony: 2', 'foddimensiony: 99999999'),
    lambda s: s.replace('foddimensionx: 2', 'foddimensionx: -2'),
    lambda s: s.replace("foddata: !nativefog '", "foddata: !nativefog '!"),
    lambda s: s.replace('  foddatas:', '  otherdata:'),
])
def test_invalid_format_stops_instead_of_guessing(broken):
    with pytest.raises(BoundaryError): apply(broken(fog_save()), 'clear')


def test_missing_or_empty_grids_are_not_claimed_as_cleared():
    for text in (SAVE, SAVE + 'gbx_discovery_pc: {foddatas: []}\n'):
        with pytest.raises(BoundaryError): apply(text, 'clear')


def test_trailing_compressed_bytes_are_rejected():
    text = fog_save()
    tree = yaml.compose(text)
    grid = member(member(tree, 'gbx_discovery_pc'), 'foddatas').value[0]
    data = member(grid, 'foddata').value
    text = text.replace(data, base64.b64encode(base64.b64decode(data) + b'trailing').decode())
    with pytest.raises(BoundaryError): apply(text, 'restore')


def test_selection_wrapper_preserves_default_and_applies_opt_in_after_protected_mission_edit():
    text = fog_save()
    default = edit(text, spec())
    chosen = spec(); chosen['fog_mode'] = 'clear'
    cleared = edit(text, chosen)
    assert pixels(default['yaml']) == bytes([0, 1, 127, 255])
    assert pixels(cleared['yaml']) == b'\xff' * 4
    assert cleared['receipt']['preserved_unowned_data']
    assert cleared['receipt']['fog']['mode'] == 'clear'
    chosen['fog_mode'] = 'invalid'
    with pytest.raises(BoundaryError): edit(text, chosen)


def test_bookmark_load_applies_fog_without_capturing_it_in_the_bookmark():
    from mission_save_bookmarks import capture
    from test_mission_save_bookmarks import SAVED, spec as bookmark_spec
    text = SAVED + 'gbx_discovery_pc:' + fog_save().split('gbx_discovery_pc:', 1)[1]
    captured = capture(text, bookmark_spec())
    assert 'foddatas' not in captured['snapshot']
    selection = dict(captured['spec'], bookmark_snapshot=captured['snapshot'], fog_mode='restore')
    assert pixels(edit(text, selection)['yaml']) == bytes(4)

"""Independent installed-file evidence and actual Epic dispatch/fail-closed gates."""
import hashlib
import importlib.resources
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2]
SDK = ROOT/'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def native(monkeypatch):
    name = 'mission_profile_test'
    package = ModuleType(name); package.__path__ = [str(SDK)]
    monkeypatch.setitem(sys.modules, name, package)
    monkeypatch.setattr(importlib.resources, 'files', lambda _: SDK)
    spec = importlib.util.spec_from_file_location(name+'.mission_native', SDK/'mission_native.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setitem(sys.modules, spec.name, m)
    return m


def test_every_mapped_address_and_fingerprint_uses_one_complete_profile(native):
    for key, profile in native.PROFILES.items():
        assert native.select_profile(profile['sha256']) == key
        runtime = NS(profile=key, base=0x100000000)
        for source, target in profile['addresses'].items():
            assert native.native_address(runtime, int(source, 16)) == runtime.base+int(target, 16)
        for source, expected in profile['fingerprints'].items():
            old = native.PROFILES[native.STEAM]['fingerprints'][source]
            assert native.native_fingerprint(runtime, int(source, 16), old) == expected
            assert native.native_fingerprint(runtime, int(source, 16), bytes.fromhex(old)) == bytes.fromhex(expected)


def test_unknown_missing_and_mixed_evidence_fail_without_a_fallback(native):
    with pytest.raises(RuntimeError, match='Unsupported executable'):
        native.select_profile('0'*64)
    for key in (None, 'epic-next'):
        with pytest.raises(RuntimeError, match='profile is unavailable'):
            native.native_address(NS(profile=key, base=0), 0x3df18e0)
    with pytest.raises(RuntimeError, match='Unmapped'):
        native.native_address(NS(profile=native.EPIC, base=0), 0x123456)
    with pytest.raises(RuntimeError, match='evidence mismatch'):
        native.native_fingerprint(NS(profile=native.EPIC, base=0), 0x3df18e0, '00'*32)


def test_all_profiles_complete_bodies_and_original_sdu_gate_match_installed_files(native):
    import pefile
    from tools.compare_native_card_builds import decode
    receipt = json.loads((ROOT/'docs/native-missions/EPIC_PROFILE.json').read_text())
    assert receipt['missing'] == [] and receipt['conflicts'] == {}
    paths = [Path(row['path']) for row in receipt['files']]
    if not all(p.is_file() for p in paths):
        pytest.skip('Both qualified executables are not installed')
    images = [pefile.PE(str(p), fast_load=True) for p in paths]
    for path, row in zip(paths, receipt['files']):
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256']
    for span in receipt['spans']:
        code = [images[i].get_data(span[k+'_rva'], span['size']) for i,k in enumerate(('steam','epic'))]
        for blob,k in zip(code,('steam','epic')):
            assert hashlib.sha256(blob).hexdigest() == span[k+'_sha256']
        assert decode(code[0],span['steam_rva'])[0] == decode(code[1],span['epic_rva'])[0]
    for key, image in zip((native.STEAM, native.EPIC), images):
        profile = native.PROFILES[key]
        for source, expected in profile['fingerprints'].items():
            assert image.get_data(int(profile['addresses'][source],16),len(bytes.fromhex(expected))).hex() == expected
    sdu=json.loads((SDK/'sdu_catalog.json').read_text())
    assert native.PROFILES[native.STEAM]['fingerprints'][sdu['native_reader_rva']] == sdu['native_reader_fingerprint']


@pytest.mark.parametrize('corrupt', [False, True])
def test_actual_runtime_constructor_selects_epic_before_native_reads(native, monkeypatch, corrupt):
    monkeypatch.setitem(sys.modules, 'mods_base', NS(ENGINE=NS(), get_pc=lambda:None))
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(make_struct=lambda *a,**k:NS(_get_address=lambda:0x20000)))
    spec = importlib.util.spec_from_file_location('mission_profile_test.mission_runtime', SDK/'mission_runtime.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    class Function:
        def __init__(self, fn): self.fn=fn
        def __call__(self,*args): return self.fn(*args)
    def filename(module, buffer, size):
        buffer.value = str(SDK/'mission_runtime.py'); return len(buffer.value)
    kernel=NS(GetModuleHandleW=Function(lambda _:0x100000000),
              GetModuleFileNameW=Function(filename),GetCurrentProcess=Function(lambda:1),
              ReadProcessMemory=Function(lambda *a:False))
    monkeypatch.setattr(m.C,'WinDLL',lambda *a,**k:kernel)
    monkeypatch.setattr(m.hashlib,'file_digest',lambda *a:NS(hexdigest=lambda:native.PROFILES[native.EPIC]['sha256']))
    seen=[]
    def read(self,address,size):
        assert self.profile == native.EPIC
        seen.append((address,size))
        for source,expected in self.manifest['fingerprints'].items():
            if address==native.native_address(self,int(source,16)):
                return b'\0'*size if corrupt else bytes.fromhex(expected)
        assert size==8
        return b'\0'*8
    monkeypatch.setattr(m.MissionRuntime,'read',read)
    if corrupt:
        with pytest.raises(RuntimeError,match='fingerprint mismatch'):
            m.MissionRuntime()
        assert len(seen)==1
    else:
        obj=m.MissionRuntime()
        assert obj.profile==native.EPIC
        assert seen[0][0] == native.native_address(obj, 0xf19ee4)
        assert (obj.base+0xcb63a08,8) in seen


@pytest.mark.parametrize('manifest,evidence_key', [
    ('mission_loader_builds.json', 'direct_evidence'),
    ('dialogue_native_builds.json', 'evidence'),
])
def test_loader_and_dialogue_complete_function_evidence_matches_both_installed_stores(manifest, evidence_key):
    import pefile
    from tools.compare_native_card_builds import decode
    data=json.loads((SDK/manifest).read_text())
    evidence=data[evidence_key]
    if evidence_key=='direct_evidence':evidence=evidence['qualification']
    assert evidence['missing']==[] and evidence['conflicts']=={}
    paths=[Path(row['path']) for row in evidence['files']]
    if not all(p.is_file() for p in paths):pytest.skip('Both qualified executables are not installed')
    images=[pefile.PE(str(p),fast_load=True) for p in paths]
    for span in evidence['spans']:
        code=[image.get_data(span[key+'_rva'],span['size']) for image,key in zip(images,('steam','epic'))]
        for blob,key in zip(code,('steam','epic')):
            assert hashlib.sha256(blob).hexdigest()==span[key+'_sha256']
        assert decode(code[0],span['steam_rva'])[0]==decode(code[1],span['epic_rva'])[0]
    for index,key in enumerate(('steam-25372571','epic-4845623')):
        entries=data['direct'][key].values() if 'direct' in data else [data['profiles'][key]]
        for entry in entries:
            assert images[index].get_data(int(entry['rva'],16),32).hex()==entry['fingerprint']

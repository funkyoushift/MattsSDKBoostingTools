import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/afk_join_stats.py'
spec = importlib.util.spec_from_file_location('join_stats_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_counter_roundtrip_and_invalid_file_preserved(tmp_path):
    path = tmp_path / 'nested' / 'stats.json'
    stats = module.JoinStats(path)
    assert stats.load() == 0
    stats.save(37)
    assert module.JoinStats(path).load() == 37
    path.write_text('{bad json')
    with pytest.raises(ValueError): stats.load()
    assert path.read_text() == '{bad json'


@pytest.mark.parametrize('value', [-1, True, 1.5, '3'])
def test_invalid_counts_rejected(tmp_path, value):
    stats = module.JoinStats(tmp_path / 'stats.json')
    with pytest.raises(ValueError): stats.save(value)
    assert not stats.path.exists()

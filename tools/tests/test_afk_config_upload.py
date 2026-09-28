import base64
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/afk_config_upload.py'


@pytest.fixture
def upload():
    spec = importlib.util.spec_from_file_location('afk_upload_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    yield mod
    for token in list(mod._uploads):
        mod._remove(token)


def stage(upload, data):
    token = upload.handle({'mode': 'begin'})['token']
    count = 0
    for offset in range(0, len(data), upload.CHUNK_BYTES):
        result = upload.handle(dict(mode='append', token=token, index=count,
            data=base64.b64encode(data[offset:offset + upload.CHUNK_BYTES]).decode()))
        count += 1
        assert result['count'] == count
    return dict(token=token, count=count, size=len(data), sha256=hashlib.sha256(data).hexdigest())


def test_multi_megabyte_lists_preserve_duplicates_order_and_unicode(upload):
    config = dict(loot=True, codes='@URandom\n' * 100000,
                  guaranteed_codes='@UMixedCase`\\\n@UMixedCase`\\\n' * 100000,
                  label='España 🎁', random_count=70)
    data = json.dumps(config, ensure_ascii=False).encode()
    assert len(data) > 2097152
    receipt = stage(upload, data)
    assert upload.consume(receipt) == config
    with pytest.raises(ValueError):
        upload.consume(receipt)


@pytest.mark.parametrize('field,value', [('count', 0), ('size', 0), ('sha256', 'wrong')])
def test_incomplete_or_corrupt_transfer_never_commits(upload, field, value):
    receipt = stage(upload, b'{"guaranteed_codes":"@UOne"}')
    receipt[field] = value
    with pytest.raises(ValueError):
        upload.consume(receipt)
    assert not upload._uploads


def test_order_cancel_and_expiry(upload):
    token = upload.handle({'mode': 'begin'})['token']
    with pytest.raises(ValueError):
        upload.handle(dict(mode='append', token=token, index=1, data='e30='))
    upload.handle(dict(mode='cancel', token=token))
    assert not upload._uploads
    receipt = stage(upload, b'{}')
    upload._uploads[receipt['token']]['time'] -= upload.TTL + 1
    with pytest.raises(ValueError):
        upload.consume(receipt)


def test_chunk_limit_does_not_limit_total_list(upload):
    token = upload.handle({'mode': 'begin'})['token']
    with pytest.raises(ValueError):
        upload.handle(dict(mode='append', token=token, index=0,
                           data=base64.b64encode(b'x' * (upload.CHUNK_BYTES + 1)).decode()))

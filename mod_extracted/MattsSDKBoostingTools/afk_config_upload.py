"""Disk-backed, ordered AFK configuration transfer. No game actions until commit."""
import base64
import hashlib
import json
import tempfile
import time
import uuid

CHUNK_BYTES = 192 * 1024
TTL = 600
_uploads = {}


def _remove(token):
    entry = _uploads.pop(token, None)
    if entry:
        entry['file'].close()


def handle(payload):
    now = time.monotonic()
    for token, entry in list(_uploads.items()):
        if now - entry['time'] > TTL:
            _remove(token)
    mode = payload.get('mode')
    if mode == 'begin':
        if len(_uploads) >= 4:
            raise ValueError('Other AFK list transfers are pending; wait or cancel them.')
        token = uuid.uuid4().hex
        _uploads[token] = dict(file=tempfile.TemporaryFile(), time=now, count=0,
                               size=0, hash=hashlib.sha256())
        return {'ok': True, 'token': token}
    token = payload.get('token')
    entry = _uploads.get(token)
    if entry is None:
        raise ValueError('AFK list transfer expired. Start again; no lists were applied.')
    entry['time'] = now
    if mode == 'cancel':
        _remove(token)
        return {'ok': True}
    if mode != 'append':
        raise ValueError('Unknown AFK list transfer operation.')
    if payload.get('index') != entry['count']:
        raise ValueError('AFK list transfer out of order; start again.')
    encoded = payload.get('data', '')
    if not isinstance(encoded, str) or len(encoded) > (CHUNK_BYTES // 3) * 4:
        raise ValueError('AFK list transfer chunk is too large.')
    data = base64.b64decode(encoded, validate=True)
    if not data:
        raise ValueError('Empty AFK list transfer chunk.')
    entry['file'].write(data)
    entry['hash'].update(data)
    entry['size'] += len(data)
    entry['count'] += 1
    return {'ok': True, 'count': entry['count']}


def consume(payload):
    token = payload.get('token')
    entry = _uploads.get(token)
    if entry is None:
        raise ValueError('AFK list transfer missing or already used; start again.')
    try:
        if (time.monotonic() - entry['time'] > TTL or
                payload.get('count') != entry['count'] or
                payload.get('size') != entry['size'] or
                payload.get('sha256') != entry['hash'].hexdigest()):
            raise ValueError('AFK list transfer incomplete; nothing applied. Start again.')
        entry['file'].seek(0)
        config = json.load(entry['file'])
        if not isinstance(config, dict):
            raise ValueError('AFK settings must be an object.')
        return config
    finally:
        _remove(token)

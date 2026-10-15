"""Source-derived experimental mission selection, independent of save progress."""
import copy
import hashlib
import json
from importlib.resources import files


def catalog():
    return json.loads(files(__package__).joinpath('mission_selection_states.json').read_text(encoding='utf-8'))


def specification(name, checkpoint):
    data = catalog()
    digest = hashlib.sha256(files(__package__).joinpath('mission_practice_catalog.json').read_bytes()).hexdigest()
    if digest != data['catalog_sha256']:
        raise RuntimeError('Mission selection data changed; rebuild its dependency catalog')
    if data.get('travel_stations_sha256') and hashlib.sha256(files(__package__).joinpath('travelstations.json').read_bytes()).hexdigest() != data['travel_stations_sha256']:
        raise RuntimeError('Replay station data changed; rebuild its location catalog')
    row = data['missions'].get(name)
    if row is None or str(checkpoint) not in row['sections']:
        raise ValueError('This section has no source-resolved map and native station')
    result = copy.deepcopy(row)
    result['section'] = result.pop('sections')[str(checkpoint)]
    if result['section'].get('spawn_issue'):
        raise ValueError(result['section']['spawn_issue'])
    result.update(catalog_sha256=digest, force_travel=True)
    return result

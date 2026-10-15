"""Audit every generated replay coordinate against its original authored record.

No game process, private save or native input is used. This verifies extracted
data/progress ownership, not collision streaming or normal encounter gameplay.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).parents[2]
MOD=ROOT/'mod_extracted/MattsSDKBoostingTools'
SOURCE=ROOT/'external_app/v22_parts_codes_fixed/matt_editor/LegitItems'


def test_every_replay_anchor_matches_its_hashed_native_source_without_future_progress():
    catalog=json.loads((MOD/'mission_practice_catalog.json').read_bytes())
    selections=json.loads((MOD/'mission_selection_states.json').read_bytes())['missions']
    docs={}
    for row in selections.values():
        past={(s.casefold(),m.casefold()) for s,m in row['past_missions']}
        for section in row['sections'].values():
            assert section['station_anchors'] and 'unresolved' not in section['station_selection']
            anchors=[*section['station_anchors']]
            if section.get('start_waypoint'):anchors.append(section['start_waypoint'])
            for anchor in anchors:
                source=anchor['source']
                if source not in docs:
                    raw=(SOURCE/source).read_bytes()
                    assert hashlib.sha256(raw).hexdigest()==catalog['source_hashes'][source]
                    docs[source]=json.loads(raw)
                native=docs[source]
                for part in anchor['pointer'].strip('/').split('/'):
                    native=native[int(part)] if isinstance(native,list) else native[part]
                assert anchor['location']=={axis:float(native['loc'][axis]) for axis in ('x','y','z')}
                assert all(math.isfinite(v) for v in anchor['location'].values())
                assert anchor['actor']==native['staticaddress'].casefold()
                assert anchor['actor'].split('.')[1]==anchor['map'].casefold()
            waypoint=section.get('start_waypoint')
            if waypoint:
                owner=waypoint['mission']
                if waypoint.get('source_rule')=='authored mission entry':
                    assert section['checkpoint']==min(int(k) for k in row['sections'])
                    entry=catalog['missions'][row['mission']]['entry_anchor']
                    assert waypoint==dict(entry,source_rule='authored mission entry')
                elif owner.casefold()==row['mission'].casefold():
                    assert waypoint['objective'].casefold() in section['past_objectives']
                else:
                    owner_data=catalog['missions'][owner]
                    assert (owner_data['mission_set'].casefold(),owner.casefold()) in past
    assert set(docs)=={'Nexus-Data-Mission0.json','Nexus-Data-Mission4.json'}

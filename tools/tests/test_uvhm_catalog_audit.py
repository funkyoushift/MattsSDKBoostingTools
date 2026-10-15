"""Compare the real rank plan with hashed extracted BL4 definitions."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_every_rank_step_and_amount_matches_extracted_game_definitions():
    tree=ast.parse((ROOT/'mod_extracted/MattsSDKBoostingTools/backend_actions.py').read_text(encoding='utf-8'))
    ranks=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.AnnAssign) and getattr(n.target,'id','')=='UVH_RANKS'))
    audit=json.loads((ROOT/'tools/mission_lab/data/uvhm_catalog_audit.json').read_bytes())
    assert [[label,list(tokens)] for label,tokens in ranks]==audit['ranks']
    positions={token:i for i,token in enumerate(token for _,tokens in ranks for token in tokens)}
    assert len(ranks)==7 and len(positions)==25
    for rank,(_label,tokens) in enumerate(ranks,1):
        for token in tokens:
            rows=audit['matches'][token];assert len(rows)==1
            row=rows[0];path=ROOT/'external_app/v22_parts_codes_fixed/matt_editor/LegitItems'/row['source']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
            definition=json.loads(path.read_bytes())
            for key in row['pointer'].strip('/').split('/'):
                definition=definition[int(key)] if isinstance(definition,list) else definition[key]
            assert definition==row['definition'] and definition['challenge']==token
            assert [tier['goalvalue'] for tier in definition['challengetiers']]==['1']
            for prerequisite in definition.get('prerequisitechallenges',[]):
                name=prerequisite.split("'")[1]
                assert name not in positions or positions[name]<positions[token]
        last=audit['matches'][tokens[-1]][0]['definition']
        assert last['bisuvhrankupchallenge']=='true'
        if rank > 1:
            assert int(last['uvhcompletionlevel'])==rank
            assert int(last['requireduvhleveltocomplete'])==rank-1
        else:
            # The extract omits the native default for rank 1. Do not invent it.
            assert 'uvhcompletionlevel' not in last

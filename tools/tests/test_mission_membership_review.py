"""A runtime overlay must not introduce new or changed objective behavior."""
from copy import deepcopy
import pytest
from tools.mission_lab.review_mission_memberships import review_reused_memberships

def definitions():
    leaf=dict(name='Leaf',completion_anchor=None)
    child=dict(name='Child',wait_for_objectives=['Leaf'],completion_anchor=None)
    root=dict(name='Root',wait_for_objectives=['Child'])
    unrelated=dict(name='Other',completion_anchor=None)
    original=dict(source='native.json',groups=[dict(index=0,objectives=[root,child,leaf,unrelated],unresolved=[]),dict(index=1,objectives=[root],unresolved=[])])
    candidate=deepcopy(original)
    candidate['groups'][1]['objectives']+=deepcopy([child,leaf])
    candidate['groups'][1]['unresolved']=[dict(objective=n,reason='missing_completion_location') for n in ('Child','Leaf')]
    return original,candidate

def test_allows_only_unchanged_transitive_reused_children_and_preserves_input():
    original,candidate=definitions();before=deepcopy(original)
    assert review_reused_memberships(original,candidate)==[(1,'Child'),(1,'Leaf')]
    assert original==before

@pytest.mark.parametrize('change',['metadata','edited_child','new_child','unrelated_child','warning','duplicate'])
def test_changed_or_unrelated_definitions_and_warning_claims_are_refused(change):
    original,candidate=definitions();group=candidate['groups'][1]
    if change=='metadata':candidate['source']='other.json'
    elif change=='edited_child':group['objectives'][1]['wait_for_objectives']=[]
    elif change=='new_child':group['objectives'].append(dict(name='New'))
    elif change=='unrelated_child':group['objectives'].append(deepcopy(original['groups'][0]['objectives'][-1]))
    elif change=='warning':group['unresolved'].append(dict(reason='assumed_ready'))
    elif change=='duplicate':group['objectives'].append(deepcopy(group['objectives'][-1]))
    with pytest.raises(ValueError):review_reused_memberships(original,candidate)

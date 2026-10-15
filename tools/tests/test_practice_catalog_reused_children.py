"""Reused composite membership must preserve its explicitly authored children."""
import importlib.util
from pathlib import Path

path=Path(__file__).resolve().parents[1]/'mission_lab/build_practice_catalog.py'
spec=importlib.util.spec_from_file_location('reused_catalog_builder',path)
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def test_reused_parent_inherits_explicit_children_in_every_group():
    definitions={'parent':[('/parent',{'objective':'Parent'})],
                 'child':[('/child',{'objective':'Child','parentobjective':'Parent'})],
                 'nested':[('/nested',{'objective':'Nested','parentobjective':'Child'})],
                 'parent_sub_guess':[('/guess',{'objective':'Parent_Sub_Guess'})]}
    first={'objectives':[{'objective':'Parent'},{'objective':'Child'}]}
    later={'objectives':[{'objective':'Parent'}]}
    expected=['Parent','Child','Nested']
    assert [o['objective'] for o in builder.group_objectives(first,definitions)]==expected
    assert [o['objective'] for o in builder.group_objectives(later,definitions)]==expected
    assert later['objectives']==[{'objective':'Parent'}]

def test_parent_cycle_terminates_without_duplicate_memberships():
    definitions={'a':[('/a',{'objective':'A','parentobjective':'B'})],
                 'b':[('/b',{'objective':'B','parentobjective':'A'})]}
    assert [o['objective'] for o in builder.group_objectives({'objectives':[{'objective':'A'}]},definitions)]==['A','B']

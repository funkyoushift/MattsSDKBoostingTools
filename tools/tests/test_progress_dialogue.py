import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
p=Path('mod_extracted/MattsSDKBoostingTools/progress_dialogue.py')
s=importlib.util.spec_from_file_location('dialogue',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Provider:
 def __init__(self,path='world:provider'):
  self.path=path;self.CurrentPerformance=NS(DialogThreadID=1,Performance='line',DialogLineRef=NS(LineName='line1'));self.calls=[]
 def _path_name(self):return self.path
 def NetMulticast_StopDialog(self,*args):self.calls.append(args)
def test_delay_and_no_repeat():
 d=m.DialogueSkipper();p=Provider()
 d.poll('job','world',[p],0);d.poll('job','world',[p],.2);assert not p.calls
 d.poll('job','world',[p],.4);d.poll('job','world',[p],1);assert p.calls==[(1,.1)]
 p.CurrentPerformance.Performance='next';d.poll('job','world',[p],2);d.poll('job','world',[p],2.4);assert len(p.calls)==2
def test_wrong_world_defaults_and_inactive():
 d=m.DialogueSkipper();ps=[Provider('other:p'),Provider('world:Default__p'),Provider()];ps[-1].CurrentPerformance.DialogThreadID=0
 d.poll('job','world',ps,0);d.poll('job','world',ps,1);assert not any(p.calls for p in ps)
def test_exception_disables_without_retry():
 d=m.DialogueSkipper();p=Provider()
 def fail(*args):p.calls.append(args);raise RuntimeError('uncertain')
 p.NetMulticast_StopDialog=fail
 d.poll('job','world',[p],0);r=d.poll('job','world',[p],1);d.poll('job','world',[p],2)
 assert r['disabled'] and len(p.calls)==1
def test_budget():
 d=m.DialogueSkipper();ps=[Provider('world:p'+str(i)) for i in range(9)]
 d.poll('job','world',ps,0);d.poll('job','world',ps,1);assert sum(len(p.calls) for p in ps)==4
 d.poll('job','world',ps,2);assert sum(len(p.calls) for p in ps)==8

def test_next_line_in_same_performance():
 d=m.DialogueSkipper();p=Provider()
 d.poll('job','world',[p],0);d.poll('job','world',[p],1)
 p.CurrentPerformance.DialogLineRef.LineName='line2'
 d.poll('job','world',[p],2);d.poll('job','world',[p],3)
 assert len(p.calls)==2

def test_playback_completion_path_observes_native_thread_end_without_provider_multicast():
 d=m.DialogueSkipper();p=Provider();p.CurrentPerformance.PlayingAudioInstance=object()
 stopped=[];playing={1:True}
 def stop(instance):stopped.append(instance);playing[1]=False
 d.poll('job','world',[p],0,stop_playback=stop,thread_playing=lambda thread:playing[thread])
 r=d.poll('job','world',[p],1,stop_playback=stop,thread_playing=lambda thread:playing[thread])
 assert len(stopped)==1 and not p.calls and r['native_thread_ends']==1 and r['skip_verified']

def test_audio_stop_alone_never_counts_as_completed_dialogue_thread():
 d=m.DialogueSkipper();p=Provider();p.CurrentPerformance.PlayingAudioInstance=object()
 d.poll('job','world',[p],0,stop_playback=lambda _:None,thread_playing=lambda _:True)
 r=d.poll('job','world',[p],1,stop_playback=lambda _:None,thread_playing=lambda _:True)
 assert not r['skip_verified'] and r['native_thread_ends']==0


def test_normal_completion_advances_each_line_without_canceling_thread():
 d=m.DialogueSkipper();p=Provider();calls=[];playing={1:True}
 def finish(provider,thread):
  calls.append((provider,thread))
  if len(calls)==2:playing[thread]=False
  return True
 d.poll('job','world',[p],0,finish_performance=finish,thread_playing=lambda t:playing[t])
 d.poll('job','world',[p],1,finish_performance=finish,thread_playing=lambda t:playing[t])
 assert len(calls)==1 and d.status()['native_thread_ends']==0 and not p.calls
 p.CurrentPerformance.DialogLineRef.LineName='two'
 d.poll('job','world',[p],2,finish_performance=finish,thread_playing=lambda t:playing[t])
 r=d.poll('job','world',[p],3,finish_performance=finish,thread_playing=lambda t:playing[t])
 assert len(calls)==2 and r['native_thread_ends']==1 and not p.calls

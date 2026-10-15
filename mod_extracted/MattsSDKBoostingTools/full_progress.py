"""Sequential full-progress coordinator; adapters own game-specific writes.

A stage returning successfully is not proof of saved 100 percent completion.
Issued stages are never automatically replayed after an uncertain result.
"""
import json
import os
import time
import uuid
from pathlib import Path

STAGES = (
    ('missions', 'Story, side and owned DLC missions'),
    ('map_locations', 'Map discoveries'),
    ('travel_stations', 'Fast-travel discoveries'),
    ('travel_requirements', 'Travel station requirements'),
    ('character', 'Levels, currencies, SDUs, vault cards and unlocks'),
    # The campaign-completion challenge unlocks UVHM's first challenge.
    ('challenges', 'All applicable challenges'),
    ('uvh', 'Ultimate Vault Hunter progression'),
    ('mayhem', 'Mayhem progression'),
    ('final_recheck', 'Newly unlocked missions and travel requirements'),
)


def eligibility(players, packs):
    if not players:
        return dict(allowed=False, reason='Load a character into the world', skipped=[])
    unavailable = [p for p in packs.values() if not p['allowed']]
    solo = len(players) <= 2
    return dict(allowed=True, solo=solo,
                reason='Only content with confirmed access for every lobby member will be completed; unavailable DLC will be skipped.',
                skipped=unavailable, blockers=[])


def compact_status(value):
    """Do not retransmit growing catalogs; durable child journals retain them."""
    if isinstance(value, list):return [compact_status(v) for v in value]
    if not isinstance(value, dict):return value
    result={}
    for key,item in value.items():
        if key in ('names','completed','initial_completed') and isinstance(item,list):
            result[key+'_count']=len(item)
        else:result[key]=compact_status(item)
    return result


class Run:
    def __init__(self, driver, folder):
        self.driver = driver
        self.folder = Path(folder)
        self.job = None

    def status(self):
        if self.job:
            return compact_status({k:v for k,v in self.job.items() if k not in ('binding', 'path')})
        pending = []
        for p in self.folder.glob('*.jsonl'):
            lines = p.read_text(encoding='utf-8').splitlines()
            if lines and json.loads(lines[-1]).get('state') not in ('finished', 'cancelled'):
                pending.append(p.stem)
        return dict(ok=not pending, state='interrupted' if pending else 'idle',
                    id=pending[0] if len(pending)==1 else None, interrupted=pending, message='Inspect interrupted progress before another run' if pending else 'Ready for preview')

    def record(self, event, **extra):
        entry=dict(event=event, state=self.job['state'], time=time.time(), **extra)
        with Path(self.job['path']).open('a', encoding='utf-8') as f:
            f.write(json.dumps(entry)+'\n'); f.flush(); os.fsync(f.fileno())

    def preview(self):
        snapshot=self.driver.preflight()
        gate=eligibility(snapshot['players'], snapshot['packs'])
        return dict(ok=True, **gate, players=snapshot['players'], stages=STAGES,
                    available_content=[p['title'] for p in snapshot['packs'].values() if p['allowed']],
                    limits=snapshot.get('limits', []), coverage=self.driver.describe(snapshot) if hasattr(self.driver,'describe') else [])

    def start(self, payload):
        if self.status()['state'] not in ('idle', 'finished', 'cancelled'):
            raise RuntimeError('A prior full-progress run needs inspection')
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Confirm that all lobby characters and shared progress will change')
        snapshot=self.driver.preflight()
        gate=eligibility(snapshot['players'],snapshot['packs'])
        if not gate['allowed']: raise ValueError(gate['reason'])
        self.driver.check_idle()
        self.folder.mkdir(parents=True,exist_ok=True)
        ident=uuid.uuid4().hex
        self.job=dict(ok=True,id=ident,state='running',index=0,total=len(STAGES),
                      phase='ready',binding=snapshot['binding'],solo=gate['solo'],
                      skipped=gate['skipped'],results=[],child=None,
                      path=str(self.folder/(ident+'.jsonl')),message='Ready to start',
                      completion_verified=False)
        self.record('start',players=snapshot['players'])
        return self.status()

    def step(self, ident):
        if not self.job or self.job['id']!=ident: raise ValueError('Run identity changed')
        if self.job['state']!='running': return self.status()
        try:
            name,title=STAGES[self.job['index']]
            if hasattr(self.driver,'observe_transition'):
                transition=self.driver.observe_transition(self.job['child'],self.job['binding'])
                if transition is not None:
                    if not transition['ready']:
                        self.job['message']=transition['message']
                        return self.status()
                    if transition['binding']!=self.job['binding']:
                        self.record('mission_map_binding',before=self.job['binding'],binding=transition['binding'])
                        self.job['binding']=transition['binding']
            snapshot=self.driver.step_snapshot(name) if hasattr(self.driver,'step_snapshot') else self.driver.preflight()
            if snapshot['binding']!=self.job['binding']: raise RuntimeError('Lobby changed; run stopped')
            gate=eligibility(snapshot['players'],snapshot['packs'])
            if not gate['allowed']: raise RuntimeError(gate['reason'])
            self.job['skipped']=gate['skipped']
            name,title=STAGES[self.job['index']]
            if self.job['phase']=='ready':
                self.record('issued',stage=name)
                self.job['phase']='issued'
                if name=='final_recheck':snapshot['prior_results']=self.job['results']
                result=self.driver.begin(name,snapshot)
            else:
                result=self.driver.poll(name,self.job['child'],snapshot)
            self.job['child']=result.get('child',self.job['child'])
            self.record('observed',stage=name,result=result)
            self.job['message']=title+': '+result.get('message','')
            if result['state']=='running': return self.status()
            if result['state']=='cancelled':
                self.job.update(state='cancelled',message='Issued work settled; remaining stages cancelled')
                self.record('cancelled')
                return self.status()
            if result['state'] not in ('finished','partial','skipped'):
                raise RuntimeError(result.get('message','Stage outcome is uncertain'))
            self.job['results'].append(dict(stage=name,**result))
            self.job.update(index=self.job['index']+1,phase='ready',child=None)
            if self.job['index']==len(STAGES):
                counts = {state: sum(r['state'] == state for r in self.job['results'])
                          for state in ('finished', 'partial', 'skipped')}
                message = (f"Run finished with {counts['partial']} incomplete and {counts['skipped']} skipped stages. "
                           if counts['partial'] or counts['skipped'] else 'All stages finished. ')
                self.job.update(state='finished', stage_summary=counts,
                    message=message + '100% completion is not verified. Review the results and check each saved character.')
            self.record('stage_finished',stage=name)
        except Exception as exc:
            message=str(exc)
            try:
                if hasattr(self.driver,'stop'):self.driver.stop(self.job.get('child'))
            except Exception as cleanup:
                message+='; selection restoration needs attention: '+str(cleanup)
            self.job.update(ok=False,state='uncertain' if self.job['phase']=='issued' else 'stopped',message=message)
            self.record('stopped',message=message,child=self.job.get('child'))
        return self.status()

    def resume(self, payload):
        if not self.job or self.job['id'] != payload.get('job_id'):
            raise ValueError('Original run is not loaded; inspect its receipt before starting another run')
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge shared progress before recovery')
        if self.job.get('cancel_requested'):
            raise RuntimeError('Cancellation is pending; restore the original selection and close this run before further work')
        if self.job['state'] not in ('stopped', 'uncertain'):
            raise ValueError('This run does not need recovery')
        if hasattr(self.driver,'observe_transition'):
            transition=self.driver.observe_transition(self.job['child'],self.job['binding'])
            if transition is not None:
                if not transition['ready']:
                    self.job['message']=transition['message']
                    return self.status()
                if transition['binding']!=self.job['binding']:
                    self.record('mission_map_binding',before=self.job['binding'],binding=transition['binding'])
                    self.job['binding']=transition['binding']
        name = STAGES[self.job['index']][0]
        snapshot = self.driver.step_snapshot(name)
        if snapshot['binding'] != self.job['binding']:
            raise ValueError('Original lobby changed; cannot resume this run')
        gate = eligibility(snapshot['players'], snapshot['packs'])
        if not gate['allowed']:
            raise ValueError(gate['reason'])
        if self.job['phase'] == 'issued':
            self.driver.recover(self.job['child'], snapshot)
        self.job.update(ok=True, state='running', message='Reconciled current work; continuing remaining stages')
        self.record('resumed', stage=name)
        return self.status()

    def close(self, payload):
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge that applied changes remain and this closes only the run record')
        ident=payload.get('job_id','')
        if not isinstance(ident,str) or len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):
            raise ValueError('Invalid run identifier')
        if self.job and self.job['state']=='running':raise RuntimeError('Stop the active run first')
        if self.job and self.job['id']==ident:
            if not self.driver.cancel(self.job.get('child')):
                raise RuntimeError('Child operation is still settling; inspect it before closing')
        self.driver.check_idle()
        path=self.folder/(ident+'.jsonl')
        if not path.is_file():raise ValueError('Run receipt not found')
        with path.open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(event='operator_closed',state='cancelled',time=time.time(),completion_verified=False))+'\n')
            f.flush();os.fsync(f.fileno())
        if self.job and self.job['id']==ident:
            self.job.update(ok=True,state='cancelled',message='Run record closed. Applied progress retained; inspect results before a new run.')
        return dict(ok=True,state='cancelled',id=ident,message='Run record closed; no game calls repeated or rolled back.')

    def cancel(self, ident):
        if not self.job or self.job['id']!=ident: raise ValueError('Run identity changed')
        if self.job['state']!='running': return self.status()
        self.job['cancel_requested']=True
        self.record('cancel_requested',child=self.job.get('child'))
        try:
            result=self.driver.cancel(self.job['child'])
        except Exception as exc:
            self.job.update(ok=False,state='uncertain',message='Cancellation cleanup needs attention: '+str(exc))
            self.record('cancel_failed',child=self.job.get('child'),message=self.job['message'])
            raise
        if not result:
            self.job.pop('cancel_requested',None)
            raise RuntimeError('Issued operation is still settling; continue verification before cancelling')
        self.job.update(state='cancelled',message='Remaining stages cancelled; applied progress retained')
        self.record('cancelled')
        return self.status()

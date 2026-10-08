"""Bounded local file bridge client. Requests expire; each session must be fresh."""
import argparse, json, os, time, uuid
from pathlib import Path
DATA=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Borderlands 4/sdk_mods/settings/MSBTFarmingLab')
def request(value):
    status=json.loads((DATA/'status.json').read_text())
    if not status['enabled'] or time.time()-status['heartbeat']>8: raise RuntimeError('Lab bridge is not live')
    ident=uuid.uuid4().hex
    value=dict(value,session=status['session'],expires=time.time()+20)
    tmp=DATA/'requests'/(ident+'.tmp');tmp.write_text(json.dumps(value));os.replace(tmp,tmp.with_suffix('.json'))
    dest=DATA/'responses'/(ident+'.json')
    end=time.monotonic()+22
    while time.monotonic()<end:
        if dest.exists(): return json.loads(dest.read_text())
        time.sleep(.15)
    raise TimeoutError('Game-thread response timed out; request has expired')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('request');parser.add_argument('--out');args=parser.parse_args()
    result=request(json.loads(args.request));text=json.dumps(result,indent=2)
    if args.out: Path(args.out).write_text(text+'\n')
    print(text)

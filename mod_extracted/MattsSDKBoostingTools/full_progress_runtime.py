"""Game-thread adapter for the full-progress coordinator."""
import json
import time
from importlib.resources import files
from . import full_progress, mission_progression as missions, mission_dlc, farming_targets
from . import backend_actions as backend, player_economy as economy, player_readback, party_helpers
from .game_parameters import MAX_PLAYER_LEVEL, MAX_SPEC_LEVEL, MAX_VAULT_CARD_LEVEL

POLICY=json.loads(files(__package__).joinpath('full_progress_policy.json').read_text())
_runner=None


def read(row):
    return player_readback.read_player(row['pc'], row['label'],
        lambda ps: party_helpers._gbc_resolve_player_display_name(ps), economy)


def content_allowed(required, snapshot):
    return required is not None and all(snapshot['packs'].get(p,{}).get('allowed',False) for p in required)


class Driver:
    def preflight(self, *, character=True):
        rows=farming_targets.resolve({'target_scope':'all'})
        from . import progress_access
        packs=progress_access.inspect(missions._engine(),rows)
        # Compare the recovered getter against the established actor/session attributes.
        established=mission_dlc.inspect(rows)
        for key,value in established.items():
            if key not in packs:continue
            if [p['access'] for p in value['players']] != [p['access'] for p in packs[key]['players']]:
                raise RuntimeError('DLC access checks disagree: '+value['title'])
            if not value['allowed']:packs[key].update(allowed=False,reason=value['reason'])
        samples=[read(r) for r in rows] if character else []
        return dict(rows=rows,players=[r['label'] for r in rows],samples=samples,
                    binding=missions._binding(rows),packs=packs,
                    limits=['Shared missions affect everyone. Two unavailable mission definitions remain excluded from completion.',
                            'Unmapped content is skipped when DLC access is incomplete.',
                            'Successful requests are reported separately from saved-character verification.'])

    def step_snapshot(self, stage):
        # Ownership and roster remain fresh on every request. Character inventories
        # are only needed by the character stage, never by discovery polling.
        return self.preflight(character=stage == 'character')

    def describe(self,snapshot):
        from . import mission_discovery
        full=all(p['allowed'] for p in snapshot['packs'].values() if p.get('required',True))
        challenges=backend._challenge_rows_for_category('All non-UVHM','')
        selected=[n for n,a in challenges if content_allowed(POLICY['challenges'].get(n,{}).get('packs'),snapshot)]
        locations=[r for r in mission_discovery.CATALOG if content_allowed(POLICY['worlds'].get(r['worldmapname']),snapshot)]
        return [f'{len(selected)} / {len(challenges)} challenge definitions selected; unavailable or unmapped content is skipped.',
                f'{len(locations)} / {len(mission_discovery.CATALOG)} discovery definitions have confirmed content access.',
                f'Character level {MAX_PLAYER_LEVEL}; specialization {MAX_SPEC_LEVEL}; available vault-card level {MAX_VAULT_CARD_LEVEL}; supported currency cap {economy._MAX_WALLET_AMOUNT:,}.',
                'Base vehicles are included. Bulk cosmetic and non-base vehicle unlocks require confirmed access to all paid content; otherwise they are reported as skipped.']

    def check_idle(self):
        if missions.status().get('state') not in ('idle','completed','cancelled','stopped'):
            raise RuntimeError('Finish or recover the current mission job first')
        if backend.complete_challenges_status()['active'] or backend.uvh_boost_status()['active'] or backend.uvh_boost_status()['paused_steps']:
            raise RuntimeError('Finish or cancel current challenge / UVH work first')

    def acceptance(self,snapshot):
        r=next((r for r in snapshot['rows'] if not r['host']),snapshot['rows'][0])
        return dict(target_scope='selected',target_player=f"{r['index']}|{r['label']}",acknowledge_shared_progress=True,reset_completed=True,settle_guest_progress=False)

    def mission_result(self,result,child):
        state=result.get('state')
        if state == 'stopped' and missions._job and missions._job.get('activation_wait') and missions._job['id'] == child['id']:
            name = missions._job['names'][missions._job['index']]
            current = missions._state(missions._row(missions._engine().snapshot(), name))
            if current in ('active', 'completed'):
                result = missions.resume(child['id'])
                state = result['state']
            elif current == 'accepted':
                missions._job.update(ok=True, state='running')
                missions._job.pop('activation_wait', None)
                result = missions._defer(name, 'Activation timed out; continuing other work and checking again in the final pass')
                state = result['state']
        if state=='running':return dict(state='running',child=child,message=result.get('message',''))
        if state=='cancelled':return dict(state='cancelled',child=child,message=result.get('message','Cancelled'))
        if state=='completed':return dict(state='finished',child=child,message=result.get('message',''),details=result)
        if state=='stopped' and (result.get('pending') or result.get('deferred')):
            return dict(state='partial',child=child,message=result.get('message',''),details=result)
        return dict(state='uncertain',child=child,message=result.get('message','Unconfirmed mission result'),details=result)

    def recover(self,child,snapshot):
        if child and child.get('kind') == 'character':
            if not child.get('pending') and child['index'] < len(snapshot['rows']):
                row = snapshot['rows'][child['index']]
                child['results'].append(dict(player=row['label'], currencies=[],
                    skipped=['Previous character request stopped after partial changes; not repeated.'],
                    message='Retained applied progress; continuing remaining players and stages'))
                child['index'] += 1
            return
        if child and child.get('kind') == 'final_recheck' and child.get('active'):
            return self.recover(child['active']['child'],snapshot)
        if not child or child.get('kind') != 'mission':
            raise RuntimeError('This operation has no verified recovery path; no calls repeated')
        status = missions.status()
        if status.get('id') != child['id']:
            raise RuntimeError('Original mission batch is not loaded')
        if status['state'] in ('running','completed'):
            return
        if status['state'] == 'stopped':
            missions.resume(child['id'])
        elif status['state'] == 'uncertain':
            missions.recover(dict(job_id=child['id'],mode='continue',acknowledge_shared_progress=True))
        else:
            raise RuntimeError('Mission batch cannot be safely continued')

    def begin(self,name,snapshot):
        if name=='final_recheck':
            done=[];mayhem_done=False
            for result in snapshot.get('prior_results',[]):
                details=result.get('details',{})
                if isinstance(details,dict):done.extend(details.get('completed',[]))
                if result['stage']=='mayhem' and result['state']=='finished':mayhem_done=True
            return dict(state='running',child=dict(kind='final_recheck',done=list(set(done)),
                        attempted=[],active=None,mayhem_done=mayhem_done,results=[],wait_since=time.monotonic()),
                        message='Checking deferred missions and travel requirements without resetting completed work')
        if name in ('missions','map_locations','travel_stations','travel_requirements'):
            payload=self.acceptance(snapshot)
            if name=='missions':payload['scope']='all'
            else:
                from . import mission_discovery
                payload['scope']=name
                planned=mission_discovery.plan(name,missions._engine().snapshot())
                if name=='travel_requirements':
                    planned=[r for r in planned if not r['blocked_reason'] and
                             (mission_dlc.requirement(r['parent'],snapshot['packs']) or {'allowed':True})['allowed']]
                else:
                    by_name={r['gbx_discovery_location_meta_data']:r for r in mission_discovery.CATALOG}
                    allowed={r['name'] for r in planned if content_allowed(POLICY['worlds'].get(by_name[r['name']]['worldmapname']),snapshot)}
                    # Never include a child whose required parent was excluded.
                    for _ in range(len(planned)):
                        remove={n for n in allowed if by_name[n]['parentlocation'] not in (None,'None','') and by_name[n]['parentlocation'] not in allowed}
                        if not remove:break
                        allowed-=remove
                    planned=[r for r in planned if r['name'] in allowed]
                if not planned:return dict(state='skipped',message='No applicable discoveries or travel requirements')
                payload['missions']=[r['name'] for r in planned]
            result=missions.start(payload)
            return self.mission_result(result,dict(kind='mission',id=result['id']))
        if name=='character':return dict(state='running',child=dict(kind=name,index=0,results=[]),message='Preparing character progress')
        if name=='uvh':
            backend._full_progress_uvh_failed=0
            backend._full_progress_queue_guard=lambda: missions._binding(farming_targets.resolve({'target_scope':'all'})) == snapshot['binding']
            for row in snapshot['rows']:
                ok,message=backend._uvh_queue_for_pc(row['pc'],list(range(len(backend.UVH_RANKS))))
                if not ok:raise RuntimeError(message)
            return dict(state='running',child=dict(kind=name),message='UVH progression queued')
        if name=='mayhem':
            if not snapshot['packs']['tuba']['allowed'] and not all(int(r['state'].HighestUnlockedMayhemLevel)>0 for r in snapshot['rows']):
                return dict(state='skipped',message='Mayhem/Takedown access is not confirmed for everyone')
            for row in snapshot['rows']:
                result=backend.mayhem_boost_target(row['pc'],row['state'],20,row['label'])
                if not result['ok']:raise RuntimeError(result['message'])
            return dict(state='finished',message='Mayhem 20 verified for each player')
        if name=='challenges':
            candidates=backend._challenge_rows_for_category('All non-UVHM','')
            full=all(p['allowed'] for p in snapshot['packs'].values() if p.get('required',True))
            selected=[(n,a) for n,a in candidates if content_allowed(POLICY['challenges'].get(n,{}).get('packs'),snapshot)]
            if not selected:return dict(state='skipped',message='No challenges with confirmed content access')
            backend._full_progress_queue_guard=lambda: missions._binding(farming_targets.resolve({'target_scope':'all'})) == snapshot['binding']
            backend._challenge_retry_failed=False
            result=backend._challenge_queue_start(selected,label='100% game challenges',targets=[r['pc'] for r in snapshot['rows']])
            if not result['ok']:raise RuntimeError(result['message'])
            return dict(state='running',child=dict(kind=name,skipped=len(candidates)-len(selected)),message=result['message'])
        raise ValueError('Unknown progress stage')

    def character(self,row,sample,snapshot):
        pc=row['pc'];ps=row['state'];results=[]
        for track,cap,label in [(0,MAX_PLAYER_LEVEL,'level'),(1,MAX_SPEC_LEVEL,'specialization')]:
            if sample.get(label) is None or sample[label]<cap:
                if not economy._set_experience_level_via_bp(ps,track,cap):raise RuntimeError('Level request failed: '+row['label'])
            results.append(label)
        tokens=['Cash','eridium']
        skipped=[]
        for card in sample['vault_cards']:
            pack=snapshot['packs'].get('banjo' if card['card']==1 else f"vaultcard{card['card']}",{})
            usable=any(p['player_id']==int(ps.PlayerId) and p['access']=='enabled' for p in pack.get('players',[]))
            if usable:
                if card['rank']<MAX_VAULT_CARD_LEVEL:
                    try:
                        card_ok=economy._set_experience_level_via_bp(ps,card['card']+1,MAX_VAULT_CARD_LEVEL)
                    except Exception:
                        card_ok=False
                    if not card_ok:
                        skipped.append(f"Vault card {card['card']} level not confirmed; activate that card and level it separately. No automatic retry.")
                tokens.append(f"VaultCard{card['card']:02d}_Tokens")
        for token in tokens:
            balance=sample['currencies'].get(token)
            if balance is None:raise RuntimeError('Currency balance is unavailable: '+token)
            delta=max(0,economy._MAX_WALLET_AMOUNT-balance)
            if delta and not economy._give_currency_on_pc(pc,token,delta):raise RuntimeError('Currency grant uncertain: '+token)
        character=economy._target_character_for_pc(pc)
        pools=character.GbxProgressionManager.ProgressPointsContainer.PointsAcquiredPerPool
        if int(pools[economy._SDU_POINTS_POOL_INDEX])<economy._MAX_SDU_POINTS:
            if not economy._set_max_sdu_points_on_pc(pc):raise RuntimeError('SDU points update failed')
        if all(p['allowed'] for p in snapshot['packs'].values() if p.get('required',True)):
            pc.ServerActivateDevPerk(4)
            ok,detail=backend._unlock_all_vehicles_for_pc(pc)
            if not ok:skipped.append('Vehicle unlocks incomplete: '+str(detail))
        else:
            from . import vehicle_tuning
            for vehicle in vehicle_tuning._load_vehicle_catalog_rows():
                if vehicle.get('category')!='base':continue
                ok,detail=vehicle_tuning._try_unlock_vehicle_for_spawn(pc,vehicle['id'],vehicle)
                if not ok:skipped.append('Vehicle unlock unconfirmed: '+vehicle['id'])
            skipped.append('Bulk cosmetic and non-base vehicle unlocks omitted because they have no per-content ownership filter')
        return dict(player=row['label'],currencies=tokens,issued_at=time.time(),message='Levels, available vault cards, currency top-ups and SDU points requested',skipped=skipped,
                    completion_verified=False)

    def poll(self,name,child,snapshot):
        if name=='final_recheck':return self.final_recheck(child,snapshot)
        if child['kind']=='mission':
            result=missions.poll(child['id'])
            return self.mission_result(result,child)
        if name=='character':
            i=child['index']
            if i >= len(snapshot['rows']):
                return dict(state='partial' if any(r['skipped'] for r in child['results']) else 'finished',
                    child=child, details=child['results'], message='Character stage finished; unconfirmed unlocks listed separately', completion_verified=False)
            if child.get('pending'):
                result=child['pending'];sample=snapshot['samples'][i]
                confirmed=(sample.get('level',0)>=MAX_PLAYER_LEVEL and sample.get('specialization',0)>=MAX_SPEC_LEVEL
                           and all(sample['currencies'].get(t)==economy._MAX_WALLET_AMOUNT for t in result['currencies']))
                if not confirmed:
                    if time.time()-result['issued_at']>10:raise RuntimeError('Character readback did not match; inspect before retry')
                    return dict(state='running',child=child,message='Waiting for character progress readback')
                child['results'].append(result);child.pop('pending');child['index']+=1
                return dict(state=('partial' if any(r['skipped'] for r in child['results']) else 'finished') if child['index']==len(snapshot['rows']) else 'running',child=child,
                            message='Level and currency readback verified; other unlocks require in-game review',details=child['results'],completion_verified=False)
            child['pending']=self.character(snapshot['rows'][i],snapshot['samples'][i],snapshot)
            return dict(state='running',child=child,message='Waiting for character progress readback')
        if name=='uvh':
            result=backend.uvh_boost_status()
            if not result['active']:backend._full_progress_queue_guard=None
            return dict(state='running' if result['active'] else 'uncertain' if backend._full_progress_uvh_failed else 'partial' if result['paused_steps'] else 'finished',child=child,details=result,
                        message=result['message'],completion_verified=False)
        if name=='challenges':
            result=backend.complete_challenges_status()
            if not result['active']:
                backend._full_progress_queue_guard=None
                backend._challenge_retry_failed=True
            return dict(state='running' if result['active'] else 'uncertain' if result['failed_count'] else 'partial' if child['skipped'] else 'finished',child=child,
                        details=result,skipped=child['skipped'],message=result['message'],completion_verified=False)
        raise RuntimeError('Unknown pending progress stage')

    def final_recheck(self,child,snapshot):
        if child['active']:
            active=child['active']
            result=self.poll(active['stage'],active['child'],snapshot)
            if result['state']=='running':
                active['child']=result.get('child',active['child'])
                return dict(state='running',child=child,message=result.get('message','Verifying final-pass work'))
            if result['state'] not in ('finished','partial','skipped'):
                return dict(state=result['state'],child=child,message=result.get('message','Final-pass result uncertain'))
            details=result.get('details',{})
            if isinstance(details,dict):child['done'].extend(details.get('completed',[]))
            child['results'].append(dict(stage=active['stage'],**result))
            child['active']=None;child['wait_since']=time.monotonic()
            return dict(state='running',child=child,message='Final-pass work verified; checking further unlocks')
        live=missions._engine().snapshot()
        excluded=set(child['done'])|set(child['attempted'])|missions.NONPERSISTENT
        remaining=[]
        for mission in missions.CATALOG:
            if mission in excluded:continue
            try:state=missions._state(missions._row(live,mission))
            except ValueError:state='unavailable'
            if state=='completed':continue
            access=mission_dlc.requirement(mission,snapshot['packs'])
            if access and not access['allowed']:
                remaining.append(dict(title=missions.CATALOG[mission]['title'],reason=access['reason']));continue
            if state not in ('available','active','accepted'):
                remaining.append(dict(title=missions.CATALOG[mission]['title'],reason='Still locked or unavailable'));continue
            payload=self.acceptance(snapshot)
            payload.update(scope='named',missions=[mission],reset_completed=False)
            child['attempted'].append(mission)
            result=missions.start(payload)
            child['active']=dict(stage='missions',child=dict(kind='mission',id=result['id']))
            return dict(state='running',child=child,message='Completing newly available mission: '+missions.CATALOG[mission]['title'])
        from . import mission_discovery
        for row in mission_discovery.plan('travel_requirements',live):
            key=row['name']
            if key in excluded:continue
            if row['blocked_reason']:
                remaining.append(dict(title=row.get('title',key),reason=row['blocked_reason']));continue
            access=mission_dlc.requirement(row['parent'],snapshot['packs'])
            if access and not access['allowed']:continue
            payload=self.acceptance(snapshot)
            payload.update(scope='travel_requirements',missions=[key],reset_completed=False)
            child['attempted'].append(key)
            result=missions.start(payload)
            child['active']=dict(stage='travel_requirements',child=dict(kind='mission',id=result['id']))
            return dict(state='running',child=child,message='Applying newly available travel requirement: '+key)
        if not child['mayhem_done']:
            # Recheck a skipped progression gate once it opens, never replay a
            # successful or uncertain Mayhem request.
            ready=snapshot['packs']['tuba']['allowed'] or all(int(r['state'].HighestUnlockedMayhemLevel)>0 for r in snapshot['rows'])
            if ready:
                child['mayhem_done']=True
                result=self.begin('mayhem',snapshot)
                if result['state']!='finished':return dict(state='uncertain',child=child,message=result.get('message','Mayhem unconfirmed'))
                child['results'].append(dict(stage='mayhem',**result));child['wait_since']=time.monotonic()
                return dict(state='running',child=child,message='Newly available Mayhem progression verified')
        if remaining and time.monotonic()-child['wait_since']<10:
            return dict(state='running',child=child,message='Waiting for final prerequisite updates')
        return dict(state='partial' if remaining or any(r['state']=='partial' for r in child['results']) else 'finished',child=child,details=child['results'],
                    skipped=remaining,message='Final recheck finished; completed work was not reset',completion_verified=False)

    def cancel(self,child):
        if child and child['kind']=='final_recheck':return self.cancel(child['active']['child'] if child['active'] else None)
        if child and child['kind']=='mission':return missions.cancel(child['id'])['state']!='running'
        if child and child['kind']=='challenges':backend.complete_challenges_cancel()
        if child and child['kind']=='uvh':
            backend.uvh_boost_cancel()
            backend._uvh_paused_queue.clear();backend._uvh_paused_targets.clear()
        backend._full_progress_queue_guard=None
        backend._challenge_retry_failed=True
        return True


def dispatch(action,payload):
    global _runner
    if _runner is None:
        from mods_base import SETTINGS_DIR
        _runner=full_progress.Run(Driver(),SETTINGS_DIR/'msbt_full_progress')
    try:
        if action=='full_progress_preview':return _runner.preview()
        if action=='full_progress_status':return _runner.status()
        if action=='full_progress_start':return _runner.start(payload)
        if action=='full_progress_step':return _runner.step(payload.get('job_id'))
        if action=='full_progress_resume':return _runner.resume(payload)
        if action=='full_progress_close':return _runner.close(payload)
        if action=='full_progress_cancel':return _runner.cancel(payload.get('job_id'))
        raise ValueError('Unknown full-progress action')
    except Exception as exc:return dict(ok=False,message=str(exc))

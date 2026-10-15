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


def challenge_plan(snapshot):
    from . import vault_card_challenges
    candidates=backend._challenge_rows_for_category('All non-UVHM','')
    def allowed(row,card):
        number=int(card.removeprefix('VaultCard'))
        pack=snapshot['packs'].get('banjo' if number==1 else f'vaultcard{number}',{})
        return any(p['player_id']==int(row['state'].PlayerId) and p['access']=='enabled' for p in pack.get('players',[]))
    vault,pools=vault_card_challenges.plan(snapshot['rows'],{n.casefold():a for n,a in candidates},allowed)
    exclusions=json.loads(files(__package__).joinpath('challenge_schedule_templates.json').read_text())
    templates=set(exclusions['names'])
    repeatable=set(exclusions['repeatable_names'])
    ordinary=[(n,a) for n,a in candidates if n.casefold() not in pools and n not in templates and n not in repeatable]
    selected=[(n,a) for n,a in ordinary if content_allowed(POLICY['challenges'].get(n,{}).get('packs'),snapshot)]
    return dict(selected=selected,skipped=len(ordinary)-len(selected),vault=vault,
                templates_excluded=len(templates),repeatable_excluded=len(repeatable))


class Driver:
    def observe_transition(self,child,binding):
        if child and child.get('kind')=='final_recheck' and child.get('active'):
            return self.observe_transition(child['active']['child'],binding)
        if not child or child.get('kind')!='mission':return None
        job=missions._job
        if not job or job['id']!=child['id']:raise RuntimeError('Original mission batch is not loaded')
        if job.get('completion_path')!='objective_graph':return None
        before=job['binding']
        if before!=binding:raise RuntimeError('Full-progress and mission lobby bindings disagree')
        from .mission_completion_context import observe
        ready=observe(missions)
        return dict(ready=ready,binding=job['binding'],message=job['message'])

    def preflight(self, *, character=True):
        rows=farming_targets.resolve({'target_scope':'all'})
        packs=mission_dlc.inspect(rows,engine=missions._engine())
        samples=[read(r) for r in rows] if character else []
        return dict(rows=rows,players=[r['label'] for r in rows],samples=samples,
                    binding=missions._binding(rows),packs=packs,
                    limits=['Shared missions affect everyone. Two legacy split definitions are excluded only when absent from the live game.',
                            'Mission completion uses the existing bulk callbacks, without replaying each objective or moving players to waypoints.',
                            'Party Reveal Map and its fog-reveal teleports are excluded from this run.',
                            'Unmapped content is skipped when DLC access is incomplete.',
                            'Successful requests are reported separately from saved-character verification.'])

    def step_snapshot(self, stage):
        # Ownership and roster remain fresh on every request. Character inventories
        # are only needed by the character stage, never by discovery polling.
        return self.preflight(character=stage == 'character')

    def describe(self,snapshot):
        from . import mission_discovery
        challenges=challenge_plan(snapshot)
        active=sum(len(t['names']) for t in challenges['vault']['tasks'])
        locations=[r for r in mission_discovery.CATALOG if content_allowed(POLICY['worlds'].get(r['worldmapname']),snapshot)]
        return [f"{len(challenges['selected'])} ordinary challenges and {active} current vault-card challenges across the selected players; inactive rotations, template definitions and repeatable loyalty rewards are excluded.",
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
        return dict(target_scope='selected',target_player=f"{r['index']}|{r['label']}",acknowledge_shared_progress=True,
                    reset_completed=True,preserve_completed=len(snapshot['rows'])==1,settle_guest_progress=False)

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
        if child and child.get('kind')=='access_refresh':
            # Poll the original acknowledgement; never repeat client requests.
            return
        if child and child.get('kind') == 'challenges' and 'readback' in child:
            vault=child.get('vault')
            if vault and (vault.get('original') or vault.get('restore_required') or vault['phase']=='uncertain' or vault['phase'].endswith('_issued')):
                raise RuntimeError('Inspect vault-card requests and original selection before recovery; no calls repeated')
            status=backend.complete_challenges_status()
            if status['active'] or status['failed_count']:
                raise RuntimeError('Challenge requests are still active or unconfirmed; no calls repeated')
            # Only the read-only phase is recoverable. Issued grants stay issued.
            return
        if child and child.get('kind') == 'character':
            if child.get('restore_required'):
                receipt=child['restore_required'];row=snapshot['rows'][child['index']]
                if (int(row['state'].PlayerId)!=receipt['player_id'] or
                    str(row['pc'].VaultCardsManager.ActivatedVaultCardDef._name)!=receipt['card']):
                    raise RuntimeError('Restore '+receipt['card']+' for '+row['label']+' before resuming; no calls repeated')
                child.pop('restore_required')
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
            if missions._job.get('completion_context',{}).get('travel_recovery'):
                result=missions.recover(dict(job_id=child['id'],mode='continue',acknowledge_shared_progress=True))
            else:result=missions.resume(child['id'])
        elif status['state'] == 'uncertain':
            result=missions.recover(dict(job_id=child['id'],mode='continue',acknowledge_shared_progress=True))
        else:
            raise RuntimeError('Mission batch cannot be safely continued')
        if result.get('state') not in ('running','completed'):
            raise RuntimeError(result.get('message','Mission recovery is still waiting; no calls repeated'))

    def begin(self,name,snapshot):
        if name=='missions' and not snapshot.get('access_refreshed'):
            from . import dlc_refresh
            return dict(state='running',child=dlc_refresh.begin(snapshot['rows']),
                        message='Refreshing visitor DLC access before completing missions')
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
            result=missions.start(payload,use_objective_graph=False)
            return self.mission_result(result,dict(kind='mission',id=result['id']))
        if name=='character':return dict(state='running',child=dict(kind=name,index=0,results=[]),message='Preparing character progress')
        if name=='uvh':
            from . import challenge_objective_complete
            missing=[row['label'] for row in snapshot['rows'] if not challenge_objective_complete.is_complete(
                row['pc'],'Challenge_Misc_World_CompleteCityEpilogue')]
            if missing:
                return dict(state='partial',skipped=missing,completion_verified=False,
                    message='Campaign completion is not confirmed for '+', '.join(missing)+
                    '; UVHM was not sent. Continuing remaining work.')
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
            planned=challenge_plan(snapshot)
            selected=planned.pop('selected')
            backend._full_progress_queue_guard=lambda: missions._binding(farming_targets.resolve({'target_scope':'all'})) == snapshot['binding']
            backend._challenge_retry_failed=False
            result=backend._challenge_queue_start(selected,label='100% game challenges',targets=[r['pc'] for r in snapshot['rows']]) if selected else dict(ok=True,message='Preparing current vault-card challenges')
            if not result['ok']:raise RuntimeError(result['message'])
            return dict(state='running',child=dict(kind=name,**planned,names=[n for n,a in selected]),message=result['message'])
        raise ValueError('Unknown progress stage')

    def character(self,row,sample,snapshot):
        pc=row['pc'];ps=row['state'];results=[]
        from . import sdu_progress
        sdu_progress.snapshot(pc, missions._engine())
        for track,cap,label in [(0,MAX_PLAYER_LEVEL,'level'),(1,MAX_SPEC_LEVEL,'specialization')]:
            if sample.get(label) is None or sample[label]<cap:
                if not economy._set_experience_level_via_bp(ps,track,cap):raise RuntimeError('Level request failed: '+row['label'])
            results.append(label)
        tokens=['Cash','eridium']
        skipped=[];vault_cards=[]
        for card in sample['vault_cards']:
            pack=snapshot['packs'].get('banjo' if card['card']==1 else f"vaultcard{card['card']}",{})
            usable=any(p['player_id']==int(ps.PlayerId) and p['access']=='enabled' for p in pack.get('players',[]))
            if usable:
                card_ok=card['rank']>=MAX_VAULT_CARD_LEVEL
                if card['rank']<MAX_VAULT_CARD_LEVEL:
                    try:
                        card_ok=economy._set_owned_vault_card_level(pc,card['card'],MAX_VAULT_CARD_LEVEL)
                    except economy.VaultCardRestoreError:
                        raise
                    except Exception:
                        card_ok=False
                    if not card_ok:
                        skipped.append(f"Vault card {card['card']} level not confirmed after activation; original selection retained. No automatic retry.")
                if card_ok:vault_cards.append(card['card'])
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
            authored={r['unlock'].casefold() for r in vehicle_tuning._load_vehicle_unlock_rows()}
            for vehicle in vehicle_tuning._load_vehicle_catalog_rows():
                if vehicle.get('category')!='base':continue
                if str(vehicle.get('unlock','')).casefold() not in authored:continue
                ok,detail=vehicle_tuning._try_unlock_vehicle_for_spawn(pc,vehicle['id'],vehicle)
                if not ok:skipped.append('Vehicle unlock unconfirmed: '+vehicle['id'])
            skipped.append('Bulk cosmetic and non-base vehicle unlocks omitted because they have no per-content ownership filter')
        return dict(player=row['label'],currencies=tokens,vault_cards=vault_cards,sdu={},issued_at=time.time(),message='Levels, available vault cards and currency top-ups requested; SDU purchases queued',skipped=skipped,
                    completion_verified=False)

    def poll(self,name,child,snapshot):
        if child['kind']=='access_refresh':
            from . import dlc_refresh
            if not dlc_refresh.ready(child['id'],snapshot['rows']):
                return dict(state='running',child=child,message='Waiting for visitor DLC access refresh')
            current=self.preflight(character=False)
            if current['binding']!=snapshot['binding']:raise RuntimeError('Lobby changed after DLC refresh')
            current['access_refreshed']=True
            return self.begin(name,current)
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
                from . import sdu_progress
                if not sdu_progress.advance(snapshot['rows'][i]['pc'], missions._engine(), result.setdefault('sdu', {})):
                    return dict(state='running', child=child, message=f"Verifying SDU upgrades: {result['sdu'].get('completed', 0)} / {result['sdu'].get('total', 59)}")
                card_ranks={c['card']:c['rank'] for c in sample.get('vault_cards',[])}
                confirmed=(sample.get('level',0)>=MAX_PLAYER_LEVEL and sample.get('specialization',0)>=MAX_SPEC_LEVEL
                           and all(sample['currencies'].get(t)==economy._MAX_WALLET_AMOUNT for t in result['currencies'])
                           and all(card_ranks.get(c,-1)>=MAX_VAULT_CARD_LEVEL for c in result.get('vault_cards',[])))
                if not confirmed:
                    if time.time()-result['issued_at']>10:raise RuntimeError('Character readback did not match; inspect before retry')
                    return dict(state='running',child=child,message='Waiting for character progress readback')
                child['results'].append(result);child.pop('pending');child['index']+=1
                return dict(state=('partial' if any(r['skipped'] for r in child['results']) else 'finished') if child['index']==len(snapshot['rows']) else 'running',child=child,
                            message='Level, currency and SDU rank readback verified; other unlocks require in-game review',details=child['results'],completion_verified=False)
            try:
                child['pending']=self.character(snapshot['rows'][i],snapshot['samples'][i],snapshot)
            except economy.VaultCardRestoreError as exc:
                child['restore_required']=dict(card=exc.original_name,player_id=int(snapshot['rows'][i]['state'].PlayerId))
                raise
            return dict(state='running',child=child,message='Waiting for character progress readback')
        if name=='uvh':
            result=backend.uvh_boost_status()
            if not result['active']:backend._full_progress_queue_guard=None
            return dict(state='running' if result['active'] else 'uncertain' if backend._full_progress_uvh_failed or result.get('uncertain') else 'partial' if result['paused_steps'] else 'finished',child=child,details=result,
                        message=result['message'],completion_verified=False)
        if name=='challenges':
            result=backend.complete_challenges_status()
            if not result['active'] and not child.get('vault'):
                backend._full_progress_queue_guard=None
                backend._challenge_retry_failed=True
            if result['active'] or result['failed_count']:
                return dict(state='running' if result['active'] else 'uncertain', child=child,
                    details=result,message=result['message'],completion_verified=False)
            from . import challenge_objective_complete
            check=child.setdefault('readback',dict(index=0,completed=0,incomplete=0,unavailable=0,samples=[]))
            batch=child['names'][check['index']:check['index']+64]
            counts=dict(completed=0,incomplete=0,unavailable=0)
            samples=[]
            for row in snapshot['rows']:
                for item in challenge_objective_complete.inspect_batch(missions._engine(),row['pc'],batch):
                    key='unavailable' if not item['exists'] else 'completed' if item['complete'] else 'incomplete'
                    counts[key]+=1
                    if key!='completed' and len(check['samples'])+len(samples)<20:
                        samples.append(dict(player=row['label'],state=key,challenge=item['name']))
            # Commit the whole party together so a failed guest read can retry
            # this batch without counting a successful host read twice.
            for key,value in counts.items():check[key]+=value
            check['samples'].extend(samples)
            check['index']+=len(batch)
            pending=check['index']<len(child['names'])
            vault=child.get('vault')
            if not pending and vault:
                from . import vault_card_challenges
                pending=not vault_card_challenges.step(vault,snapshot['rows'],
                    lambda event: _runner.record('vault_card_'+event,child=child))
                if not pending:
                    backend._full_progress_queue_guard=None
                    backend._challenge_retry_failed=True
            message=(f"Native challenge readback: {check['completed']} complete, "
                     f"{check['incomplete']} not complete, {check['unavailable']} unavailable. "
                     + (f"Current vault-card challenges: {vault['verified']} verified; inactive rotations excluded. " if vault else '')
                     + 'Saved guest progress is unverified.')
            return dict(state='running' if pending else 'partial' if child['skipped'] or check['incomplete'] or check['unavailable'] or (vault and vault['skipped']) else 'finished',
                child=child,details=result,skipped=child['skipped'],message=message,completion_verified=False)
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
            if missions._automatic_exclusion(live,mission):continue
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
            result=missions.start(payload,use_objective_graph=False)
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
            result=missions.start(payload,use_objective_graph=False)
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
        if child and child['kind']=='access_refresh':
            from . import dlc_refresh
            dlc_refresh.cancel(child['id'])
        if child and child['kind']=='final_recheck':return self.cancel(child['active']['child'] if child['active'] else None)
        if child and child['kind']=='mission':return missions.cancel(child['id'])['state']!='running'
        if child and child['kind']=='challenges':
            backend.complete_challenges_cancel()
            if child.get('vault'):
                from . import vault_card_challenges
                vault_card_challenges.restore(child['vault'],farming_targets.resolve({'target_scope':'all'}),
                    lambda event: _runner.record('vault_card_'+event,child=child))
        if child and child['kind']=='uvh':
            backend.uvh_boost_cancel()
            backend._uvh_paused_queue.clear();backend._uvh_paused_targets.clear()
        backend._full_progress_queue_guard=None
        backend._challenge_retry_failed=True
        return True

    def stop(self,child):
        if child and child.get('kind')=='access_refresh':
            from . import dlc_refresh
            dlc_refresh.cancel(child['id'])
        if child and child.get('kind')=='challenges' and child.get('vault'):
            from . import vault_card_challenges
            vault_card_challenges.restore(child['vault'],farming_targets.resolve({'target_scope':'all'}),
                lambda event: _runner.record('vault_card_'+event,child=child))


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

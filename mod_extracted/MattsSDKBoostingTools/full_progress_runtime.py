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


def challenge_audit(payload):
    """Read one bounded slice of native challenge state without issuing grants."""
    from . import challenge_objective_complete
    snapshot=Driver().preflight(character=False)
    selected=challenge_plan(snapshot)['selected']
    try:offset=int(payload.get('offset',0))
    except (TypeError,ValueError):raise ValueError('Invalid challenge audit offset')
    if offset<0 or offset>len(selected):raise ValueError('Invalid challenge audit offset')
    names=[name for name,_amount in selected[offset:offset+64]]
    rows=[]
    for player in snapshot['rows']:
        for item in challenge_objective_complete.inspect_batch(missions._engine(),player['pc'],names):
            if not item['exists'] or not item['complete']:
                rows.append(dict(player=player['label'],challenge=item['name'],
                                 state='unavailable' if not item['exists'] else 'incomplete'))
    next_offset=offset+len(names)
    return dict(ok=True,offset=offset,next_offset=next_offset if next_offset<len(selected) else None,
                total=len(selected),players=snapshot['players'],binding=snapshot['binding'],rows=rows,
                message='Read-only native challenge audit; no progress changed')


def mission_credit_probe(payload):
    """Read native once-only mission credit for a bounded authored challenge set."""
    from . import mission_challenges
    snapshot=Driver().preflight(character=False)
    challenge_ids=payload.get('challenge_ids')
    results=mission_challenges.inspect_mission_credit_catalog(
        missions._engine(),snapshot['rows'],challenge_ids,
        definition_details=payload.get('definition_details') is True)
    return dict(ok=True,players=snapshot['players'],binding=snapshot['binding'],
                results=results,message='Read-only native mission credit probe; no progress changed')


def challenge_probe(payload):
    """Inspect a few current native progress records without issuing events."""
    from . import challenge_objective_complete
    snapshot=Driver().preflight(character=False)
    names=payload.get('challenge_ids')
    if not isinstance(names,list) or not 1<=len(names)<=8:
        raise ValueError('Inspect between one and eight challenges')
    allowed={name for name,_ in challenge_plan(snapshot)['selected']}
    if any(not isinstance(name,str) or name not in allowed for name in names):
        raise ValueError('Challenge is outside the selected lobby catalog')
    engine=missions._engine()
    return dict(ok=True,players=snapshot['players'],binding=snapshot['binding'],
                results=[dict(player=row['label'],challenges=
                    challenge_objective_complete.inspect_exact_progress(engine,row['pc'],names))
                         for row in snapshot['rows']],
                message='Read-only native challenge progress probe; no progress changed')


def mission_credit_plan(snapshot):
    """Plan only missing once-only credits whose live rules and missions agree."""
    from . import mission_challenges
    engine=missions._engine()
    shared=engine.snapshot()
    selected={name for name,_ in challenge_plan(snapshot)['selected']}
    plan=[];issues=[]
    for entry in mission_challenges.MISSION_CREDIT_CATALOG['entries']:
        challenge=entry['challenge']
        if challenge not in selected:continue
        definition=mission_challenges.credit_definition(challenge)
        try:
            players=[mission_challenges.read_player(engine,row['pc'],definition)
                     for row in snapshot['rows']]
        except RuntimeError as exc:
            if str(exc)=='Challenge player is not ready':raise
            issues.append(dict(challenge=challenge,reason=str(exc)[:200]))
            continue
        missing={index for player in players for index in range(len(definition['missions']))
                 if index not in player['credited']}
        names=[]
        for index in sorted(missing):
            name=definition['missions'][index]
            try:completed=missions._state(missions._row(shared,name))=='completed'
            except ValueError:completed=False
            access=mission_dlc.requirement(name,snapshot['packs'])
            if not completed or access and not access['allowed']:
                issues.append(dict(challenge=challenge,mission=name,
                                   reason='Shared mission completion or lobby content access is unconfirmed'))
                continue
            names.append(name)
        if names:plan.append(dict(challenge=challenge,missions=names))
    return plan,issues


def fact_trigger_plan(snapshot, incomplete):
    """Experimental live shortfall planner; not called by automatic Full Game."""
    from . import challenge_objective_complete
    if not incomplete:return [],[]
    engine=missions._engine()
    if getattr(engine,'profile',None)!='steam-26007962':
        return [],[dict(reason='Exact FactTrigger repair is unqualified for this game build')]
    plan=[];issues=[]
    for row in snapshot['rows']:
        names=list(dict.fromkeys(item['challenge'] for item in incomplete
                                  if item['player']==row['label']))
        for start in range(0,len(names),8):
            batch=names[start:start+8]
            try:results=challenge_objective_complete.inspect_exact_progress(
                engine,row['pc'],batch)
            except RuntimeError as exc:
                issues.extend(dict(player=row['label'],challenge=name,reason=str(exc)[:200])
                              for name in batch)
                continue
            for item in results:
                if not item.get('exists') or not item.get('progress_present'):
                    issues.append(dict(player=row['label'],challenge=item['challenge'],
                                       reason=item.get('reason','Native progress unavailable')))
                    continue
                if item['definition_type']!=14:
                    continue
                count=item['native_count'];goal=item['final_goal']
                if (item['tier_count']<1 or not isinstance(goal,int) or
                        item['record_count']!=count or not 0<=count<goal or
                        item['gate_11']!=0 or item['gate_18']<0 or item['gate_28']!=1):
                    issues.append(dict(player=row['label'],challenge=item['challenge'],
                                       reason='Native FactTrigger shortfall is not safe to increment'))
                    continue
                plan.append(dict(player=row['label'],challenge=item['challenge'],
                                 amount=goal-count,expected_goal=goal))
    return plan,issues


class Driver:
    def pending_child(self,stage):
        if stage not in ('missions','map_locations','travel_stations','travel_requirements'):
            return None
        current=missions.status()
        if current.get('id') and current.get('state') not in ('idle','completed','cancelled','stopped'):
            return dict(kind='mission',id=current['id'])
        return None

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
        engine=missions._engine()
        packs=mission_dlc.inspect(rows,engine=engine)
        samples=[read(r) for r in rows] if character else []
        limits=[]
        if engine.profile in ('steam-26007962', 'epic-6d531d91'):
            limits.append('Current game build: mission, discovery and challenge catalogs still come from 1.10. New or changed content is not yet covered by this Full Game run.')
        limits.extend([
            'Shared missions affect everyone. Two legacy split definitions are excluded only when absent from the live game.',
            'Mission completion uses the existing bulk callbacks, without replaying each objective or moving players to waypoints.',
            'Party Reveal Map and its fog-reveal teleports are excluded from this run.',
            'Unmapped content is skipped when DLC access is incomplete.',
            'Successful requests are reported separately from saved-character verification.'])
        return dict(rows=rows,players=[r['label'] for r in rows],samples=samples,
                    binding=missions._binding(rows),packs=packs,
                    limits=limits)

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
        uvh = backend.uvh_boost_status()
        if (backend.complete_challenges_status()['active'] or uvh['active'] or
                (uvh['paused_steps'] and not uvh['uncertain'])):
            raise RuntimeError('Finish or cancel current challenge / UVH work first')

    def close_interrupted(self,events):
        """Close only the mission receipt owned by this interrupted Full Game run."""
        status=missions.status()
        if status.get('state')!='interrupted':return
        def owned_mission(candidate):
            if candidate.get('kind')=='mission':return candidate
            if candidate.get('kind')=='challenges':
                active=candidate.get('credit_active')
                return dict(kind='mission',id=active['id']) if isinstance(active,dict) and active.get('id') else None
            if candidate.get('kind')=='final_recheck':
                active=candidate.get('active')
                nested=active.get('child') if isinstance(active,dict) else None
                return owned_mission(nested) if isinstance(nested,dict) else None
            return None
        child=None
        for event in reversed(events):
            candidate=event.get('child')
            if not isinstance(candidate,dict):
                result=event.get('result')
                candidate=result.get('child') if isinstance(result,dict) else None
            if isinstance(candidate,dict):
                child=owned_mission(candidate)
                break
        if not child or status.get('id')!=child.get('id'):
            raise RuntimeError('Interrupted mission receipt does not match this Full Game run')
        missions.recover(dict(job_id=child['id'],mode='close',
            acknowledge_shared_progress=True))

    def prepare_start(self, *, replace_other_progress=False):
        notes=[]
        if replace_other_progress:
            mission=missions.status()
            if mission.get('state')=='running':
                stopped=missions.cancel(mission['id'])
                notes.append(dict(kind='mission',message=stopped.get('message','Mission run stopped; applied progress retained.')))
                if stopped.get('state')=='running':
                    raise RuntimeError('Mission work is still settling; check its status before starting Full Game')
            challenge=backend.complete_challenges_status()
            if challenge['active']:
                stopped=backend.complete_challenges_cancel()
                notes.append(dict(kind='challenges',message=stopped['message'],discarded_steps=challenge['steps_remaining']))
            uvh=backend.uvh_boost_status()
            if uvh['active']:
                backend.uvh_boost_cancel()
                uvh=backend.uvh_boost_status()
            if uvh['paused_steps']:
                result=backend.uvh_boost_discard_paused(allow_manual=True)
                if not result['ok']:
                    raise RuntimeError(result['message'])
                notes.append(dict(kind='uvh',**result))
            return notes
        uvh = backend.uvh_boost_status()
        if not (uvh['paused_steps'] and uvh['uncertain']):
            return notes
        result = backend.uvh_boost_discard_paused()
        if not result['ok']:
            raise RuntimeError(result['message'])
        return [dict(kind='uvh',**result)]

    def acceptance(self,snapshot):
        r=next((r for r in snapshot['rows'] if not r['host']),snapshot['rows'][0])
        return dict(target_scope='selected',target_player=f"{r['index']}|{r['label']}",acknowledge_shared_progress=True,
                    reset_completed=True,preserve_completed=len(snapshot['rows'])==1,settle_guest_progress=False,
                    defer_unconfirmed_mission_credit=True,continue_on_mission_failure=True)

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
        if state=='completed':
            pending=result.get('unverified_challenge_credit',[])
            operations=result.get('unverified_operations',[])
            message=result.get('message','')
            if pending:message+=f'; {len(pending)} mission credit readback(s) unresolved; final pass will recheck'
            if operations:message+=f'; {len(operations)} mission operation(s) unresolved; final pass will inspect without retry'
            return dict(state='partial' if pending or operations else 'finished',child=child,message=message,details=result)
        if state=='stopped' and (result.get('pending') or result.get('deferred')):
            return dict(state='partial',child=child,message=result.get('message',''),details=result)
        return dict(state='uncertain',child=child,message=result.get('message','Unconfirmed mission result'),details=result)

    def recover(self,child,snapshot):
        if child and child.get('kind')=='access_refresh':
            # Poll the original acknowledgement; never repeat client requests.
            return
        if child and child.get('kind')=='challenges' and child.get('credit_active'):
            active=child['credit_active']
            status=missions.status()
            if status.get('id')!=active['id']:
                raise RuntimeError('Original mission credit receipt is not loaded')
            if status['state'] in ('uncertain','interrupted'):
                result=missions.recover(dict(job_id=active['id'],mode='close',
                                             acknowledge_shared_progress=True))
                if not result.get('closed'):
                    raise RuntimeError('Mission credit remains uncertain; no callback repeated')
                child.setdefault('credit_issues',[]).append(dict(
                    challenge=active['challenge'],reason='Issued credit was closed unverified after recovery'))
                child['credit_active']=None
                child['credit_index']+=1
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
        if child and child.get('kind') == 'final_recheck':
            if child.get('credit_active'):
                from . import mission_challenges
                mission_challenges.reconcile(missions._engine(),snapshot['rows'],child['credit_active'],
                    lambda event:_runner.record('challenge_credit_recheck',details=event))
                child['credit_active']=None
            if child.get('active'):
                return self.recover(child['active']['child'],snapshot)
            return
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
        if result.get('state') not in ('running','completed') and not (
                result.get('state')=='stopped' and result.get('deferred')):
            raise RuntimeError(result.get('message','Mission recovery is still waiting; no calls repeated'))

    def begin(self,name,snapshot):
        if name=='missions' and not snapshot.get('access_refreshed'):
            from . import dlc_refresh
            return dict(state='running',child=dlc_refresh.begin(snapshot['rows']),
                        message='Refreshing visitor DLC access before completing missions')
        if name=='final_recheck':
            done=[];mayhem_done=False;credits=[];operations=[]
            for result in snapshot.get('prior_results',[]):
                details=result.get('details',{})
                if isinstance(details,dict):
                    done.extend(details.get('completed',[]))
                    credits.extend(details.get('unverified_challenge_credit',[]))
                    operations.extend(details.get('unverified_operations',[]))
                if result['stage']=='mayhem' and result['state']=='finished':mayhem_done=True
            return dict(state='running',child=dict(kind='final_recheck',done=list(set(done)),
                        attempted=[],active=None,mayhem_done=mayhem_done,results=[],wait_since=time.monotonic(),
                        credit_pending=list({(r['mission'],r.get('player_id'),r.get('player_path')):r for r in credits}.values()),credit_index=0,
                        credit_active=None,credit_unverified=[],operation_pending=operations,
                        operation_index=0,operation_unverified=[]),
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
            from . import mission_challenges
            # Once-only Mission definitions need the native per-mission event;
            # generic counter increments returned successfully but left guest
            # achievements incomplete in the live two-player run.
            bulk=[row for row in selected if row[0] not in mission_challenges.MISSION_CREDIT_DEFINITIONS]
            backend._full_progress_queue_guard=lambda: missions._binding(farming_targets.resolve({'target_scope':'all'})) == snapshot['binding']
            backend._challenge_retry_failed=False
            result=backend._challenge_queue_start(bulk,label='100% game challenges',targets=[r['pc'] for r in snapshot['rows']]) if bulk else dict(ok=True,message='Preparing current vault-card challenges')
            if not result['ok']:raise RuntimeError(result['message'])
            return dict(state='running',child=dict(kind=name,**planned,names=[n for n,a in selected]),message=result['message'])
        raise ValueError('Unknown progress stage')

    def mission_credit_repair(self,child,snapshot):
        """Repair validated missing Mission bits before challenge readback."""
        if child.get('credit_done'):return None
        if 'credit_plan' not in child:
            try:plan,issues=mission_credit_plan(snapshot)
            except RuntimeError as exc:
                if str(exc)!='Challenge player is not ready':raise
                since=child.setdefault('credit_ready_since',time.monotonic())
                if time.monotonic()-since<10:
                    return dict(state='running',child=child,message='Waiting for joined player challenge records')
                plan=[];issues=[dict(reason='Joined player challenge records did not become ready')]
            child.update(credit_plan=plan,credit_index=0,credit_issues=issues,credit_active=None)
        if child['credit_active']:
            active=child['credit_active']
            result=missions.poll(active['id'])
            if result['state']=='running':
                return dict(state='running',child=child,message=result.get('message','Checking mission credit'))
            if result['state']!='completed' or result.get('unverified_challenge_credit'):
                child['credit_issues'].append(dict(challenge=active['challenge'],
                                                   reason=result.get('message','Mission credit was not fully verified')))
            if result['state']=='uncertain':
                # An issued native callback may still settle. Stop the run
                # until its durable receipt can be reconciled or closed.
                return dict(state='uncertain',child=child,message=result.get('message','Mission credit is uncertain'))
            child['credit_active']=None
            child['credit_index']+=1
        if child['credit_index']<len(child['credit_plan']):
            item=child['credit_plan'][child['credit_index']]
            payload=self.acceptance(snapshot)
            payload.update(scope='challenge_credit',challenge_id=item['challenge'],
                           missions=item['missions'],mode='complete',reset_completed=False,
                           preserve_completed=False)
            try:result=missions.start(payload,use_objective_graph=False)
            except (RuntimeError,ValueError) as exc:
                child['credit_issues'].append(dict(challenge=item['challenge'],reason=str(exc)[:200]))
                child['credit_index']+=1
                return dict(state='running',child=child,message='Mission credit group unavailable; continuing')
            child['credit_active']=dict(id=result['id'],challenge=item['challenge'])
            return dict(state='running',child=child,message='Repairing validated mission credits: '+item['challenge'])
        child['credit_done']=True
        return None

    def fact_trigger_repair(self,child,snapshot):
        """Experimental callback path; not called by automatic Full Game."""
        if child.get('fact_repair_done'):return None
        from . import challenge_objective_complete
        if 'fact_repair_plan' not in child:
            plan,issues=fact_trigger_plan(snapshot,child['readback']['incomplete_names'])
            child.update(fact_repair_plan=plan,fact_repair_index=0,
                         fact_repair_issues=issues,fact_repair_active=None)
            if not plan:
                child['fact_repair_done']=True
                return None
        active=child['fact_repair_active']
        if active:
            status=backend.complete_challenges_status()
            if status['active']:
                return dict(state='running',child=child,message='Completing exact native challenge shortfall')
            row=next((r for r in snapshot['rows'] if r['label']==active['player']),None)
            if row is None:raise RuntimeError('Challenge repair player left the lobby')
            if status['failed_count']:
                child['fact_repair_issues'].append(dict(player=active['player'],
                    challenge=active['challenge'],reason=status['message']))
            else:
                try:item=challenge_objective_complete.inspect_exact_progress(
                    missions._engine(),row['pc'],[active['challenge']])[0]
                except RuntimeError as exc:
                    if time.monotonic()-active['issued_at']<10:
                        return dict(state='running',child=child,
                                    message='Waiting for native challenge readback')
                    item=dict(native_complete=False)
                    child['fact_repair_issues'].append(dict(player=active['player'],
                        challenge=active['challenge'],reason=str(exc)[:200]))
                if not item.get('native_complete'):
                    if time.monotonic()-active['issued_at']<10:
                        return dict(state='running',child=child,
                                    message='Waiting for native challenge completion')
                    if not any(issue.get('player')==active['player'] and
                               issue.get('challenge')==active['challenge'] for issue in child['fact_repair_issues']):
                        child['fact_repair_issues'].append(dict(player=active['player'],
                            challenge=active['challenge'],reason='Issued challenge did not complete'))
            child['fact_repair_active']=None
            child['fact_repair_index']+=1
        if child['fact_repair_index']<len(child['fact_repair_plan']):
            item=child['fact_repair_plan'][child['fact_repair_index']]
            row=next((r for r in snapshot['rows'] if r['label']==item['player']),None)
            if row is None:raise RuntimeError('Challenge repair player left the lobby')
            try:current=challenge_objective_complete.inspect_exact_progress(
                missions._engine(),row['pc'],[item['challenge']])[0]
            except RuntimeError as exc:
                child['fact_repair_issues'].append(dict(player=item['player'],
                    challenge=item['challenge'],reason=str(exc)[:200]))
                child['fact_repair_index']+=1
                return dict(state='running',child=child,message='Challenge readback unavailable; continuing')
            if current.get('native_complete'):
                child['fact_repair_index']+=1
                return dict(state='running',child=child,message='Challenge already settled')
            if (current.get('definition_type')!=14 or current.get('final_goal')!=item['expected_goal']
                    or current.get('record_count')!=current.get('native_count')
                    or current.get('gate_11')!=0 or current.get('gate_18',-1)<0
                    or current.get('gate_28')!=1
                    or not 0<=current.get('native_count',-1)<item['expected_goal']):
                child['fact_repair_issues'].append(dict(player=item['player'],
                    challenge=item['challenge'],reason='Native challenge changed before repair'))
                child['fact_repair_index']+=1
                return dict(state='running',child=child,message='Challenge changed; continuing')
            amount=item['expected_goal']-current['native_count']
            backend._full_progress_queue_guard=lambda: missions._binding(
                farming_targets.resolve({'target_scope':'all'}))==snapshot['binding']
            backend._challenge_retry_failed=False
            result=backend._challenge_queue_start([(item['challenge'],amount)],
                label='Exact challenge shortfall',targets=[row['pc']])
            if not result['ok']:
                child['fact_repair_issues'].append(dict(player=item['player'],
                    challenge=item['challenge'],reason=result['message']))
                child['fact_repair_index']+=1
                return dict(state='running',child=child,message='Challenge repair unavailable; continuing')
            child['fact_repair_active']=dict(**item,issued_at=time.monotonic())
            return dict(state='running',child=child,message='Completing exact challenge shortfall')
        child['fact_repair_done']=True
        child['fact_repair_before']=child.pop('readback')
        return dict(state='running',child=child,message='Rechecking challenge completion after repair')

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
            credit=self.mission_credit_repair(child,snapshot)
            if credit is not None:return credit
            from . import challenge_objective_complete
            check=child.setdefault('readback',dict(index=0,completed=0,incomplete=0,unavailable=0,
                                                  samples=[],incomplete_names=[]))
            check.setdefault('incomplete_names',[])
            batch=child['names'][check['index']:check['index']+64]
            counts=dict(completed=0,incomplete=0,unavailable=0)
            samples=[]
            incomplete_names=[]
            for row in snapshot['rows']:
                for item in challenge_objective_complete.inspect_batch(missions._engine(),row['pc'],batch):
                    key='unavailable' if not item['exists'] else 'completed' if item['complete'] else 'incomplete'
                    counts[key]+=1
                    if key=='incomplete' and len(check['incomplete_names'])+len(incomplete_names)<64:
                        incomplete_names.append(dict(player=row['label'],challenge=item['name']))
                    if key!='completed' and len(check['samples'])+len(samples)<20:
                        samples.append(dict(player=row['label'],state=key,challenge=item['name']))
            # Commit the whole party together so a failed guest read can retry
            # this batch without counting a successful host read twice.
            for key,value in counts.items():check[key]+=value
            check['samples'].extend(samples)
            check['incomplete_names'].extend(incomplete_names)
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
            # Native FactTrigger increments reached a live-complete state but
            # the host's two exact-goal completions disappeared on Save/Quit.
            # Keep the read-only audit; automatic repair needs a proven saved
            # progress path before it can run in Full Game again.
            message=(f"Native challenge readback: {check['completed']} complete, "
                     f"{check['incomplete']} not complete, {check['unavailable']} unavailable. "
                     + (f"Current vault-card challenges: {vault['verified']} verified; inactive rotations excluded. " if vault else '')
                     + 'Native challenge completion in this lobby does not confirm saved completion.')
            return dict(state='running' if pending else 'partial' if child['skipped'] or check['incomplete'] or check['unavailable'] or child.get('credit_issues') or child.get('fact_repair_issues') or (vault and vault['skipped']) else 'finished',
                child=child,details=result,skipped=(child['skipped']+len(child.get('credit_issues',[]))
                    +len(child.get('fact_repair_issues',[]))),message=message,completion_verified=False)
        raise RuntimeError('Unknown pending progress stage')

    def final_recheck(self,child,snapshot):
        from . import mission_challenges
        child.setdefault('credit_pending',[])
        child.setdefault('credit_index',0)
        child.setdefault('credit_active',None)
        child.setdefault('credit_unverified',[])
        child.setdefault('operation_pending',[])
        child.setdefault('operation_index',0)
        child.setdefault('operation_unverified',[])
        if child['credit_index']<len(child['credit_pending']):
            item=child['credit_pending'][child['credit_index']]
            name=item['mission']
            journal=lambda event:_runner.record('challenge_credit_recheck',details=event)
            if child['credit_active']:
                try:
                    mission_challenges.reconcile(missions._engine(),snapshot['rows'],child['credit_active'],journal)
                except mission_challenges.CreditPending:
                    return dict(state='running',child=child,message='Waiting for native mission credit verification')
                child['credit_active']=None
            party=snapshot['rows']
            if item.get('player_id') is not None:
                party=[r for r in party if int(r['state'].PlayerId)==item['player_id']
                       and r['pc']._path_name()==item.get('player_path')]
                if len(party)!=1:
                    child['credit_unverified'].append(dict(title=missions.CATALOG[name]['title'],
                        reason='Player left or changed before mission credit recheck'))
                    child['credit_index']+=1
                    return dict(state='running',child=child,message='Mission credit player unavailable; continuing final checks')
            live=missions._engine().snapshot()
            if missions._state(missions._row(live,name))!='completed':
                child['credit_unverified'].append(dict(title=missions.CATALOG[name]['title'],reason='Mission completion no longer reads completed; credit was not retried'))
                child['credit_index']+=1
                return dict(state='running',child=child,message='Mission credit not reissued because mission completion changed')
            try:
                mission_challenges.credit_completed(missions._engine(),party,name,journal)
            except mission_challenges.CreditReadbackMismatch as exc:
                child['credit_unverified'].append(dict(title=missions.CATALOG[name]['title'],reason=str(exc)))
                child['credit_index']+=1
                return dict(state='running',child=child,message='Mission credit still disagrees; continuing other final checks')
            except mission_challenges.CreditPending as exc:
                child['credit_active']=exc.receipt
                return dict(state='running',child=child,message='Verifying one native mission credit callback')
            child['credit_index']+=1
            return dict(state='running',child=child,message='Mission credit readback verified')
        if child['operation_index'] < len(child['operation_pending']):
            item=child['operation_pending'][child['operation_index']]
            child['operation_index']+=1
            verified=False
            if item.get('operation')=='safehouse_claim' and item.get('address'):
                try:
                    from . import mission_effects
                    host=next(r['pc'] for r in snapshot['rows'] if r['host'])
                    observed=mission_effects.inspect_safehouse_claim(
                        host,item['mission'],item['address'])
                    verified=observed['state'].casefold()=='claimed'
                    _runner.record('operation_recheck',details=dict(
                        mission=item['mission'],operation=item['operation'],
                        channel=observed['channel'],observed=observed['state']))
                except Exception as exc:
                    _runner.record('operation_recheck_error',details=dict(
                        mission=item['mission'],operation=item['operation'],error=str(exc)[:500]))
            if not verified:
                child['operation_unverified'].append(dict(
                    title=item['title'],reason='Operation remains unverified; no game call repeated',
                    operation=item.get('operation')))
            return dict(state='running',child=child,message=(
                'Mission side effect verified by readback' if verified else
                'Mission side effect remains unverified; continuing final checks'))
        if child['active']:
            active=child['active']
            result=self.poll(active['stage'],active['child'],snapshot)
            if result['state']=='running':
                active['child']=result.get('child',active['child'])
                return dict(state='running',child=child,message=result.get('message','Verifying final-pass work'))
            if result['state'] not in ('finished','partial','skipped'):
                return dict(state=result['state'],child=child,message=result.get('message','Final-pass result uncertain'))
            details=result.get('details',{})
            if isinstance(details,dict):
                child['done'].extend(details.get('completed',[]))
                known={(r['mission'],r.get('player_id'),r.get('player_path')) for r in child['credit_pending']}
                child['credit_pending'].extend(r for r in details.get('unverified_challenge_credit',[])
                    if (r['mission'],r.get('player_id'),r.get('player_path')) not in known)
                child['operation_pending'].extend(details.get('unverified_operations',[]))
            child['results'].append(dict(stage=active['stage'],**result))
            child['active']=None;child['wait_since']=time.monotonic()
            return dict(state='running',child=child,message='Final-pass work verified; checking further unlocks')
        live=missions._engine().snapshot()
        excluded=(set(child['done'])|set(child['attempted'])|missions.NONPERSISTENT|
                  {r['mission'] for r in child['operation_pending']})
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
        unresolved=remaining+child['credit_unverified']+child['operation_unverified']
        return dict(state='partial' if unresolved or any(r['state']=='partial' for r in child['results']) else 'finished',child=child,details=child['results'],
                    skipped=unresolved,message='Final recheck finished; completed work was not reset',completion_verified=False)

    def cancel(self,child):
        if child and child['kind']=='access_refresh':
            from . import dlc_refresh
            dlc_refresh.cancel(child['id'])
        if child and child['kind']=='final_recheck':
            if child.get('credit_active'):
                from . import mission_challenges
                try:
                    mission_challenges.reconcile(missions._engine(),farming_targets.resolve({'target_scope':'all'}),
                        child['credit_active'],lambda event:_runner.record('challenge_credit_recheck',details=event))
                except mission_challenges.CreditPending:
                    return False
                child['credit_active']=None
            return self.cancel(child['active']['child'] if child['active'] else None)
        if child and child['kind']=='mission':
            state=missions.status().get('state')
            if state in ('uncertain','interrupted'):
                return missions.recover(dict(job_id=child['id'],mode='close',
                    acknowledge_shared_progress=True)).get('closed',False)
            return missions.cancel(child['id'])['state']!='running'
        if child and child['kind']=='challenges':
            if child.get('credit_active'):
                active=child['credit_active']
                result=missions.cancel(active['id'])
                if result.get('state')=='running':return False
                if result.get('state') in ('uncertain','interrupted'):
                    if not missions.recover(dict(job_id=active['id'],mode='close',
                            acknowledge_shared_progress=True)).get('closed',False):
                        return False
                elif result.get('state') not in ('cancelled','completed','stopped'):
                    return False
                child['credit_active']=None
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
    if action in ('full_progress_challenge_audit','full_progress_mission_credit_probe','full_progress_challenge_probe'):
        try:
            if action=='full_progress_challenge_audit':return challenge_audit(payload)
            if action=='full_progress_mission_credit_probe':return mission_credit_probe(payload)
            return challenge_probe(payload)
        except Exception as exc:return dict(ok=False,message=str(exc))
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

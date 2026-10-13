"""Reviewed checkpoint actor repair; no whole-world spawn reset.

Zadra proof: docs/changes/2026-10-13-mission-practice-selector.md.
The later One Fell Swoop despawn remains in the world after ordinary replay.
Clearing that block before resetting/re-enabling the authored lab node restored
normal Talk to Zadra gameplay. This is a tested replay repair, not a claim that
every world fact has been restored to its original serialized default.
"""
MISSION = 'Mission_Main_Grasslands2'
CHECKPOINT = 22
GROUP = 'Grasslands_Main2'
SPAWN = 'Grasslands_Main2_Zadra_ZadraLab'
DESPAWN = 'Grasslands_Main2_Zadra_HQDeSpawn'
NPC_GROUP = 'Grasslands_Main'
NPC = 'Grasslands_Main_Zadra_NPC'


def _node(sdk):
    matches=[]
    for node in sdk.find_all('GbxAINodeComponent',exact=False):
        conduit=node.FactsConduit
        if (str(conduit.GroupName.Name)==GROUP and
                str(conduit.RegistryName.Name.Name)==SPAWN):
            matches.append(node)
    if len(matches)>1:raise RuntimeError('Zadra spawn identity is ambiguous')
    if not matches:return None
    node=matches[0]
    if (str(node.SpawnedActorGroupName.Name)!=NPC_GROUP or
            str(node.SpawnedActorRegistryName.Name)!=NPC):
        raise RuntimeError('Zadra spawn registry differs from the reviewed checkpoint')
    return node


def ready(job,journal):
    if job['name']!=MISSION or job['checkpoint']!=CHECKPOINT:return True
    import unrealsdk
    from mods_base import get_pc
    node=_node(unrealsdk)
    if node is None:
        job['message']='Loading Zadra’s authored spawn node at the checkpoint.'
        return False
    if node.GetSpawnedActor() is not None:return True
    if job.get('zadra_repair_returned'):
        job['message']='Waiting for Zadra to spawn; the issued repair will not repeat.'
        return False
    if job.get('zadra_repair_issued'):
        raise RuntimeError('Zadra repair has an uncertain result; inspect before repeating it')
    pc=get_pc()
    if pc is None:return False
    lib=unrealsdk.find_object('FactsBlueprintLibrary','/Script/GbxGame.Default__FactsBlueprintLibrary')
    def address(actor,channel):return '.'.join(('registry','World_P','top',GROUP,actor,channel))
    def read(addr):return str(lib.ReadFact(OwnerContext=pc,AddressString=addr,AsName='None',AsInt=0,AsBool=False)[1])
    facts=[(address(DESPAWN,'DisableSpawning'),'FALSE'),
           (address(DESPAWN,'Enabled'),'FALSE'),(address(SPAWN,'Enabled'),'TRUE')]
    before={addr:read(addr) for addr,_ in facts}
    if any(value not in ('None','TRUE','FALSE') for value in before.values()):
        raise RuntimeError('Unknown Zadra spawn state; repair not issued')
    job.update(state='uncertain',ok=False,zadra_repair_issued=True)
    journal(dict(event='zadra_repair_issued',before=before,node=node._path_name()))
    def write(addr,value):
        journal(dict(event='zadra_fact_issued',address=addr,value=value))
        lib.WriteFact(OwnerContext=pc,AddressString=addr,AsName=value,AsInt=0,AsBool=False)
        after=read(addr)
        journal(dict(event='zadra_fact_returned',address=addr,after=after))
        if after!=value:raise RuntimeError('Zadra spawn fact did not match; inspect the repair receipt')
    for addr,value in facts[:2]:
        if before[addr]=='TRUE':write(addr,value)
    spawn=facts[2][0]
    write(spawn,'FALSE')
    journal(dict(event='zadra_native_reset_issued'))
    node.ResetNodeSpawn()
    journal(dict(event='zadra_native_reset_returned'))
    write(spawn,'TRUE')
    job.update(state='running',ok=True,zadra_repair_returned=True,
               message='Waiting for Zadra’s normal checkpoint spawn.')
    journal(dict(event='zadra_repair_returned'))
    return node.GetSpawnedActor() is not None

"""Review-build console access to the same mission backend used by the app."""
import json

from mods_base import command


@command('msbt_missions', description='Preview or test shared mission progress. Run affects host and party; review build limits jobs to two missions.')
def mission_command(args):
    from .backend_actions import run_quick_menu_action
    from unrealsdk import logging
    payload = dict(scope=args.scope, missions=args.mission, reset_completed=args.reset_completed,
                   target_scope='local' if args.player == 'local' else 'selected',
                   acknowledge_shared_progress=True)
    if args.player != 'local':
        payload['target_player'] = args.player
    if args.operation in ('status', 'cancel'):
        result = run_quick_menu_action('mission_status', {}, record=False)
        if args.operation == 'cancel' and result.get('id'):
            result = run_quick_menu_action('mission_cancel', {'job_id': result['id']}, record=False)
    elif args.operation == 'preview':
        result = run_quick_menu_action('mission_preview', payload, record=False)
    else:
        result = run_quick_menu_action('mission_start', payload, record=False)
        # Review build only: at most two missions / six guarded native steps.
        # The app uses separate mission_step requests for responsive progress.
        for _ in range(6):
            if not result.get('ok') or result.get('state') != 'running':
                break
            result = run_quick_menu_action('mission_step', {'job_id': result['id']}, record=False)
        if result.get('state') == 'running':
            result = run_quick_menu_action('mission_cancel', {'job_id': result['id']}, record=False)
    logging.info('[MSBT Missions] ' + json.dumps(result, ensure_ascii=False))


mission_command.add_argument('operation', choices=('preview', 'run', 'status', 'cancel'))
mission_command.add_argument('--scope', choices=('current', 'named', 'story', 'sides', 'dlc', 'all'), default='current')
mission_command.add_argument('--mission', action='append', default=[])
mission_command.add_argument('--player', default='local', help='Exact player name or local; all shared party progress may change')
mission_command.add_argument('--reset-completed', action='store_true', help='Reset a completed host mission before normal acceptance')

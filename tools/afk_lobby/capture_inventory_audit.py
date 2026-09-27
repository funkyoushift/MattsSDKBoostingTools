"""Run a read-only inventory audit against a locally installed test SDK.

AFK boosting must be stopped. Saves item codes locally; never prints them.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.request


def action(payload):
    data = json.dumps({'action': 'afk_inventory_audit', 'payload': payload, 'timeout': 8}).encode()
    request = urllib.request.Request('http://127.0.0.1:49774/action', data=data,
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=12) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError(result.get('message') or 'Inventory check failed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--player-index', type=int, help='Explicit guest index from the bridge roster')
    target.add_argument('--compare', help='Capture again using the original audit ID and guest identity')
    parser.add_argument('--output', type=Path, default=Path('output/inventory-audits'))
    args = parser.parse_args()
    api_inventory = action({'mode': 'apis'})
    request = {'mode': 'compare', 'audit_id': args.compare} if args.compare else {'mode': 'start', 'player_index': args.player_index}
    audit = action(request)['audit']
    audit_id = audit['id']
    complete = False
    try:
        deadline = time.monotonic() + 330
        while time.monotonic() < deadline:
            audit = action({'mode': 'status', 'audit_id': audit_id})['audit']
            if audit['phase'] == 'complete':
                captured = action({'mode': 'snapshot', 'audit_id': audit_id})
                captured['native_api_names'] = api_inventory
                args.output.mkdir(parents=True, exist_ok=True)
                path = args.output / f'{audit_id}-{time.time_ns()}.json'
                with path.open('x', encoding='utf-8') as stream:
                    json.dump(captured, stream, indent=2, ensure_ascii=False)
                complete = True
                print(f'Read-only capture saved: {path.resolve()}')
                print(f"Rows: {len(captured['snapshot']['rows'])}. No inventory was changed.")
                return
            if audit['phase'] in ('failed', 'cancelled'):
                raise RuntimeError(audit['error'])
            time.sleep(.5)
        raise TimeoutError('Inventory capture did not finish')
    finally:
        if not complete:
            try:
                action({'mode': 'cancel', 'audit_id': audit_id})
            except Exception:
                pass


if __name__ == '__main__':
    main()

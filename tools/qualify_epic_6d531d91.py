"""Read-only current Steam/Epic mission qualification. Never opens a process."""
import json
from pathlib import Path

import qualify_mission_builds as q


def main():
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / 'docs/native-missions/STEAM_26007962_PROFILE.json').read_text())
    addresses = {int(k, 16): int(v, 16) for k, v in baseline['addresses'].items()}
    extra = tuple(int(row['target_steam_rva'], 16) for row in baseline['loader_dialogue_spans'])
    receipt = q.qualify(
        Path(baseline['target']['path']),
        Path('C:/Program Files/Epic Games/Venus/OakGame/Binaries/Win64/Borderlands4.exe'),
        expected=(baseline['target']['sha256'],
                  '6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e'),
        code=tuple(addresses[x] for x in q.CODE) + extra,
        vtables=tuple(addresses[x] for x in q.VTABLES),
        tokens=tuple(addresses[x] for x in q.TOKENS))
    if receipt['missing'] or receipt['conflicts']:
        raise RuntimeError('Incomplete or conflicting correspondence; no receipt updated')
    output = root / 'docs/native-missions/EPIC_6D531D91_PROFILE.json'
    output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Offline qualified {len(receipt["addresses"])} locations, {len(receipt["spans"])} bodies; no live proof')


if __name__ == '__main__':
    main()

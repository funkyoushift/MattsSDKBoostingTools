import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_mission_credit_catalog import build_catalog


def _write_source(folder: Path, filename: str, records: list[tuple[str, dict]]) -> Path:
    entries = [{challenge: {"challenge": challenge, **record}} for challenge, record in records]
    payload = {"challenge": {"records": [{"entries": entries}]}}
    path = folder / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _record(**overrides):
    record = {
        "challengetype": "Mission",
        "busecustommissionlist": "true",
        "bcompleteeachmissiononce": "true",
        "missiondefs": ["mission'Mission_One'", "mission'Mission_Two'"],
    }
    record.update(overrides)
    return record


class MissionCreditCatalogTests(unittest.TestCase):
    def test_filters_and_preserves_authored_order_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            source = _write_source(source_dir, "Nexus-Data-challenge4.json", [
                ("challenge_mission", _record()),
                ("challenge_not_once", _record(bcompleteeachmissiononce="false")),
                ("challenge_other_type", _record(challengetype="FactTrigger")),
            ])
            _write_source(source_dir, "Nexus-Data-challenge_list.json", [("skip", _record())])

            catalog = build_catalog(source_dir)

            self.assertEqual(catalog["game_build"], 25234898)
            self.assertEqual(len(catalog["entries"]), 1)
            entry = catalog["entries"][0]
            self.assertEqual(entry["challenge"], "challenge_mission")
            self.assertEqual(entry["missions"], ["Mission_One", "Mission_Two"])
            self.assertEqual(entry["source"], source.name)
            self.assertEqual(entry["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(entry["pointer"], "/challenge/records/0/entries/0/challenge_mission")
            self.assertIn("1.10", entry["provenance"])

    def test_generation_is_deterministic_and_authored_file_order_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            _write_source(source_dir, "Nexus-Data-challenge6.json", [("later", _record())])
            _write_source(source_dir, "Nexus-Data-challenge0.json", [("earlier", _record())])
            first = json.dumps(build_catalog(source_dir), sort_keys=True)
            second = json.dumps(build_catalog(source_dir), sort_keys=True)
            self.assertEqual(first, second)
            challenges = [entry["challenge"] for entry in build_catalog(source_dir)["entries"]]
            self.assertEqual(challenges, ["earlier", "later"])

    def test_rejects_duplicate_ids_and_invalid_mission_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            _write_source(source_dir, "Nexus-Data-challenge0.json", [("duplicate", _record())])
            _write_source(source_dir, "Nexus-Data-challenge4.json", [("duplicate", _record())])
            with self.assertRaisesRegex(ValueError, "duplicate challenge ID"):
                build_catalog(source_dir)

        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            _write_source(source_dir, "Nexus-Data-challenge0.json", [
                ("bad_token", _record(missiondefs=["Mission_One"]))
            ])
            with self.assertRaisesRegex(ValueError, "invalid mission token"):
                build_catalog(source_dir)


if __name__ == "__main__":
    unittest.main()

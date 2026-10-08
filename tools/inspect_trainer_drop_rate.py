"""Read-only trainer/game evidence extraction. Never runs or patches either EXE.

Requires development-only pefile and capstone. Writes a JSON research receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64


def inspect(trainer: Path, game: Path) -> dict:
    trainer_bytes = trainer.read_bytes()
    game_bytes = game.read_bytes()
    image = pefile.PE(data=game_bytes, fast_load=True)
    exception = image.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    # Read only RUNTIME_FUNCTION triples; parsing every unwind record is unnecessary.
    functions = list(struct.iter_unpack("<III", image.get_data(exception.VirtualAddress, exception.Size)))
    scripts = []
    for match in re.finditer(rb"\[ENABLE\][^\x00]+", trainer_bytes):
        if b"aobscanmodule(aobdroprate," in match.group():
            scripts.append({"file_offset": hex(match.start()), "text": match.group().decode("ascii")})
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    sites = []
    for script in scripts:
        signature = re.search(r"aobscanmodule\(aobdroprate,Borderlands4.exe,([^\)]+)\)", script["text"]).group(1)
        pattern = re.compile(b"".join(b"." if token == "*" else re.escape(bytes.fromhex(token))
                                      for token in signature.split()), re.DOTALL)
        matches = []
        for section in image.sections:
            if not section.Characteristics & 0x20000000:
                continue
            data = section.get_data()
            for match in pattern.finditer(data):
                rva = section.VirtualAddress + match.start()
                function = next((entry for entry in functions if entry[0] <= rva < entry[1]), None)
                begin = function[0] if function else rva
                end = function[1] if function else rva + 128
                # Decode from a recovered function boundary, never arbitrary mid-instruction bytes.
                code = image.get_data(begin, min(end - begin, 0x10000))
                instructions = [
                    {"rva": hex(ins.address - image.OPTIONAL_HEADER.ImageBase),
                     "bytes": ins.bytes.hex(" "), "instruction": f"{ins.mnemonic} {ins.op_str}"}
                    for ins in disassembler.disasm(code, image.OPTIONAL_HEADER.ImageBase + begin)
                    if rva - 96 <= ins.address - image.OPTIONAL_HEADER.ImageBase <= rva + 128
                ]
                matches.append({"rva": hex(rva), "file_offset": hex(section.PointerToRawData + match.start()),
                                "function_begin_rva": hex(begin), "function_end_rva": hex(end),
                                "instructions": instructions})
        sites.append({"trainer_script_offset": script["file_offset"], "signature": signature, "matches": matches})
    return {
        "mode": "read-only offline extraction; neither executable executed",
        "trainer": {"path": str(trainer), "sha256": hashlib.sha256(trainer_bytes).hexdigest(), "scripts": scripts},
        "game": {"path": str(game), "sha256": hashlib.sha256(game_bytes).hexdigest(),
                 "timestamp": image.FILE_HEADER.TimeDateStamp, "size_of_image": image.OPTIONAL_HEADER.SizeOfImage},
        "sites": sites,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trainer", required=True, type=Path)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = inspect(args.trainer, args.game)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(args.output), "trainer_sha256": result["trainer"]["sha256"],
                      "game_sha256": result["game"]["sha256"],
                      "match_rvas": [[m["rva"] for m in s["matches"]] for s in result["sites"]]}))

#!/usr/bin/env python3
"""Census of the Solana programs in a SlopDotCash/slopdotcash checkout.

Usage: python3 scripts/solana-program-census.py <checkout>

Mechanically cross-checks, at whatever commit the checkout is on:

- the Anchor workspace under contracts/solana (Anchor.toml, Cargo.toml,
  programs/*) against the checked-in IDL (idl/slop_escrow.json),
- the program module's instruction functions, the #[account] state
  structs, the #[event] structs and the EscrowError variants in
  programs/slop-escrow/src/lib.rs against the same IDL,
- the Anchor discriminator convention (sha256 of "global:<name>",
  "account:<Name>", "event:<Name>") for every IDL entry,
- the off-chain reviewed-program pin in contracts/solana/programs.ts
  against the declared program ID,
- which files outside contracts/solana import the Solana adapter layer.

Prints the census and CENSUS PASSED when every cross-check holds;
exits 1 otherwise. No dependencies beyond the standard library.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

# Helper functions that live outside the #[program] module in lib.rs and
# therefore must NOT appear in the IDL instruction list.
KNOWN_NON_PROGRAM_FNS = {
    "award_id_for",
    "monthly_message",
    "monthly_release_message",
    "monthly_leaf",
}


def fail(msg):
    print(f"CENSUS FAILED: {msg}")
    sys.exit(1)


def sha8(text):
    return list(hashlib.sha256(text.encode()).digest()[:8])


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    root = Path(sys.argv[1])
    sol = root / "contracts" / "solana"
    if not sol.is_dir():
        fail(f"{sol} not found")

    # --- Anchor workspace -------------------------------------------------
    anchor_toml = (sol / "Anchor.toml").read_text()
    sections = re.findall(r"\[programs\.([a-z0-9-]+)\]", anchor_toml)
    entries = re.findall(
        r"\[programs\.[a-z0-9-]+\]\s*\n([a-z_]+)\s*=\s*\"([1-9A-HJ-NP-Za-km-z]{32,44})\"",
        anchor_toml,
    )
    print(f"Anchor.toml program sections: {sections}")
    print(f"Anchor.toml program entries:  {entries}")
    if len(entries) != 1:
        fail("expected exactly one declared program in Anchor.toml")
    prog_key, program_id = entries[0]

    cargo = (sol / "Cargo.toml").read_text()
    if 'members = ["programs/*"]' not in cargo:
        fail("workspace members is not programs/*")
    program_dirs = sorted(
        p.name for p in (sol / "programs").iterdir() if p.is_dir()
    )
    print(f"programs/ directories: {program_dirs}")
    if len(program_dirs) != 1:
        fail("expected exactly one program crate")

    lib_rs_path = sol / "programs" / program_dirs[0] / "src" / "lib.rs"
    lib_rs = lib_rs_path.read_text()

    m = re.search(r'declare_id!\("([1-9A-HJ-NP-Za-km-z]{32,44})"\)', lib_rs)
    if not m:
        fail("declare_id! not found")
    declared_id = m.group(1)
    print(f"declare_id!: {declared_id}")
    if declared_id != program_id:
        fail("declare_id! does not match Anchor.toml")

    # --- IDL cross-check ---------------------------------------------------
    idl = json.loads((sol / "idl" / "slop_escrow.json").read_text())
    if idl.get("address") != declared_id:
        fail("IDL address does not match declare_id!")
    idl_ix = [i["name"] for i in idl["instructions"]]
    print(f"IDL instructions ({len(idl_ix)}): {idl_ix}")

    pub_fns = re.findall(r"pub fn ([a-z_0-9]+)\s*\(", lib_rs)
    extra = set(pub_fns) - set(idl_ix)
    if extra != KNOWN_NON_PROGRAM_FNS:
        fail(f"non-IDL pub fns differ from known helpers: {sorted(extra)}")
    if set(pub_fns) & set(idl_ix) != set(idl_ix):
        fail("some IDL instructions have no pub fn in lib.rs")
    print("source pub fns == IDL instructions + 4 known non-program helpers")

    for ix in idl["instructions"]:
        if ix["discriminator"] != sha8(f"global:{ix['name']}"):
            fail(f"instruction discriminator mismatch: {ix['name']}")
    print("all instruction discriminators == sha256('global:<name>')[..8]")

    account_structs = re.findall(
        r"#\[account\](?:\s*#\[[^\]]*\])*\s*pub struct ([A-Z][A-Za-z0-9]*)",
        lib_rs,
    )
    idl_accounts = [a["name"] for a in idl["accounts"]]
    print(f"#[account] structs ({len(account_structs)}): {account_structs}")
    print(f"IDL accounts ({len(idl_accounts)}): {idl_accounts}")
    if set(account_structs) != set(idl_accounts):
        fail("account struct set differs from IDL accounts")
    for a in idl["accounts"]:
        disc = a.get("discriminator") or []
        if disc and disc != sha8(f"account:{a['name']}"):
            fail(f"account discriminator mismatch: {a['name']}")
    print("all account discriminators == sha256('account:<Name>')[..8]")

    event_structs = re.findall(
        r"#\[event\](?:\s*#\[[^\]]*\])*\s*pub struct ([A-Z][A-Za-z0-9]*)",
        lib_rs,
    )
    idl_events = [e["name"] for e in idl["events"]]
    print(f"#[event] structs ({len(event_structs)}): {event_structs}")
    print(f"IDL events ({len(idl_events)}): {idl_events}")
    if set(event_structs) != set(idl_events):
        fail("event struct set differs from IDL events")
    for e in idl["events"]:
        if e["discriminator"] != sha8(f"event:{e['name']}"):
            fail(f"event discriminator mismatch: {e['name']}")
    print("all event discriminators == sha256('event:<Name>')[..8]")

    enum_body = re.search(
        r"pub enum EscrowError \{(.*?)\n\}", lib_rs, re.S
    )
    if not enum_body:
        fail("EscrowError enum not found")
    variants = re.findall(r"^\s+([A-Z][A-Za-z0-9]*)\s*,?\s*$", enum_body.group(1), re.M)
    # variants carry #[msg("...")] attributes; keep only bare variant lines
    variants = [v for v in variants if not v.startswith("Msg")]
    idl_errors = idl["errors"]
    print(f"EscrowError variants ({len(variants)}), IDL errors ({len(idl_errors)})")
    if [e["name"] for e in idl_errors] != variants:
        fail("IDL error names differ from EscrowError variants (or order)")
    if [e["code"] for e in idl_errors] != [6000 + i for i in range(len(variants))]:
        fail("IDL error codes are not 6000..6000+n-1 in order")
    print("IDL errors == EscrowError variants in order, codes 6000..")

    seeds = sorted(set(re.findall(r'b"([a-z_]+)"', lib_rs)))
    print(f"PDA seed literals in lib.rs: {seeds}")

    # --- Off-chain reviewed pin -------------------------------------------
    programs_ts = (sol / "programs.ts").read_text()
    pins = re.findall(r'programId:\s*"([1-9A-HJ-NP-Za-km-z]{32,44})"', programs_ts)
    networks = re.findall(r'network:\s*"([^"]+)"', programs_ts)
    code_hashes = re.findall(r"codeSha256:\s*\n?\s*\"([0-9a-f]{64})\"", programs_ts)
    print(f"programs.ts reviewed pins: networks={networks} programIds={pins}")
    print(f"programs.ts codeSha256 values: {code_hashes}")
    if pins != [declared_id]:
        fail("programs.ts does not pin exactly the declared program ID")
    if networks != ["solana-mainnet"]:
        fail("programs.ts pin network is not exactly ['solana-mainnet']")
    if len(code_hashes) != 1:
        fail("expected exactly one codeSha256 pin in programs.ts")

    # --- Platform connection ----------------------------------------------
    importers = []
    for base in ("backend", "src", "workers", "functions", "scripts"):
        bdir = root / base
        if not bdir.is_dir():
            continue
        for f in bdir.rglob("*"):
            if f.suffix not in (".ts", ".tsx", ".mts", ".mjs", ".js"):
                continue
            try:
                text = f.read_text(errors="ignore")
            except OSError:
                continue
            if "contracts/solana/" in text:
                mods = sorted(set(re.findall(r"contracts/solana/([a-z0-9-]+)", text)))
                importers.append((str(f.relative_to(root)), mods))
    print("files outside contracts/solana importing the adapter layer:")
    for path, mods in importers:
        print(f"  {path}: {mods}")
    if not any(p.startswith("backend/payments/") for p, _ in importers):
        fail("no backend/payments importer of the Solana adapter layer found")

    print("CENSUS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

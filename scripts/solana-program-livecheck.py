#!/usr/bin/env python3
"""Live check of the reviewed Solana program pin against public RPC.

Usage: python3 scripts/solana-program-livecheck.py <checkout> [--rpc URL]

Reads the declared program ID from the checkout's
contracts/solana/Anchor.toml and the reviewed pin (programId, codeSha256,
upgradeAuthority, identityAuthority, feeRecipient, rotationAuthority)
from contracts/solana/programs.ts, then queries a public Solana JSON-RPC
endpoint (default: api.mainnet-beta.solana.com, finalized commitment):

- the program account (owner must be the upgradeable loader, executable),
- its ProgramData account (address read from the program account and
  also re-derived as a PDA): last-deploy slot, upgrade authority, and
  SHA-256 of the code region after the 45-byte loader header — the same
  comparison contracts/solana/adapter.ts performs before use,
- the singleton Config PDA (seeds [b"config"]): the Anchor account
  discriminator and the three authority fields are parsed and compared
  with the pin.

Prints every observed value and LIVECHECK PASSED when all comparisons
match; exits 1 otherwise. Read-only: it never sends a transaction.
Standard library only.
"""

import base64
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_RPC = "https://api.mainnet-beta.solana.com"
LOADER_UPGRADEABLE = "BPFLoaderUpgradeab1e11111111111111111111111"
PROGRAMDATA_HEADER = 45  # loader header size; cf. adapter.ts content.slice(45)

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s):
    n = 0
    for c in s:
        n = n * 58 + B58.index(c)
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + n.to_bytes((n.bit_length() + 7) // 8, "big")


def b58encode(b):
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\x00"))) + (out or "")


_P = 2**255 - 19
_D = (-121665 * pow(121666, _P - 2, _P)) % _P


def is_on_curve(b):
    y = int.from_bytes(b, "little") & _P
    sign = b[31] >> 7
    yy = (y * y) % _P
    xx = ((yy - 1) * pow((_D * yy + 1) % _P, _P - 2, _P)) % _P
    if xx == 0:
        return sign == 0
    return pow(xx, (_P - 1) // 2, _P) == 1


def find_program_address(seeds, program_id_b):
    for bump in range(255, -1, -1):
        h = hashlib.sha256(
            b"".join(seeds) + bytes([bump]) + program_id_b + b"ProgramDerivedAddress"
        ).digest()
        if not is_on_curve(h):
            return b58encode(h), bump
    raise ValueError("no PDA found")


class Rpc:
    def __init__(self, url):
        self.url = url

    def call(self, method, params):
        req = urllib.request.Request(
            self.url,
            data=json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.load(r)
        if "error" in out:
            raise RuntimeError(f"RPC error: {out['error']}")
        return out["result"]

    def account(self, addr):
        res = self.call(
            "getAccountInfo",
            [addr, {"commitment": "finalized", "encoding": "base64"}],
        )
        return res.get("value"), res.get("context", {}).get("slot")


def parse_config_account(data):
    """Parse an Anchor Config account: 8-byte discriminator, three
    pubkeys (identity authority, fee recipient, rotation authority),
    one bump byte. Returns a dict of base58 strings plus the raw bump."""
    disc = hashlib.sha256(b"account:Config").digest()[:8]
    if data[:8] != disc:
        raise ValueError("Config discriminator mismatch")
    return {
        "identity_authority": b58encode(data[8:40]),
        "fee_recipient": b58encode(data[40:72]),
        "rotation_authority": b58encode(data[72:104]),
        "bump": data[104],
    }


def read_pin(checkout):
    sol = Path(checkout) / "contracts" / "solana"
    anchor = (sol / "Anchor.toml").read_text()
    m = re.search(r'slop_escrow\s*=\s*"([1-9A-HJ-NP-Za-km-z]{32,44})"', anchor)
    program_id = m.group(1)
    ts = (sol / "programs.ts").read_text()

    def field(name):
        m = re.search(name + r':\s*\n?\s*"([^"]+)"', ts)
        return m.group(1) if m else None

    pin = {
        "program_id": program_id,
        "network": field("network"),
        "code_sha256": field("codeSha256"),
        "upgrade_authority": field("upgradeAuthority"),
        "identity_authority": field("identityAuthority"),
        "fee_recipient": field("feeRecipient"),
        "rotation_authority": field("rotationAuthority"),
    }
    return pin


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rpc_url = DEFAULT_RPC
    if "--rpc" in sys.argv:
        rpc_url = sys.argv[sys.argv.index("--rpc") + 1]
    if len(args) != 1:
        print(__doc__)
        return 1
    pin = read_pin(args[0])
    print(f"pin from checkout: {json.dumps(pin, indent=2)}")
    if pin["network"] != "solana-mainnet" and rpc_url == DEFAULT_RPC:
        print("note: pin network is not solana-mainnet; RPC default still mainnet")

    rpc = Rpc(rpc_url)
    slot = rpc.call("getSlot", [{"commitment": "finalized"}])
    print(f"finalized context slot: {slot}")

    failures = []

    def check(label, observed, expected):
        ok = observed == expected
        print(f"{label}: observed={observed} expected={expected} -> {'OK' if ok else 'MISMATCH'}")
        if not ok:
            failures.append(label)

    prog, _ = rpc.account(pin["program_id"])
    if prog is None:
        print("LIVECHECK FAILED: program account not found")
        return 1
    print(f"program: owner={prog['owner']} executable={prog['executable']}")
    check("program owner", prog["owner"], LOADER_UPGRADEABLE)
    check("program executable", prog["executable"], True)

    pdata = base64.b64decode(prog["data"][0])
    pd_addr = b58encode(pdata[4:36])
    derived, _ = find_program_address(
        [b58decode(pin["program_id"])], b58decode(LOADER_UPGRADEABLE)
    )
    print(f"programdata address: from-account={pd_addr} derived={derived}")
    check("programdata address", pd_addr, derived)

    pd, _ = rpc.account(pd_addr)
    raw = base64.b64decode(pd["data"][0])
    deploy_slot = int.from_bytes(raw[4:12], "little")
    authority = b58encode(raw[13:45]) if raw[12] == 1 else None
    code_hash = hashlib.sha256(raw[PROGRAMDATA_HEADER:]).hexdigest()
    print(f"programdata: last_deploy_slot={deploy_slot} upgrade_authority={authority}")
    print(f"programdata: code region bytes={len(raw) - PROGRAMDATA_HEADER} sha256={code_hash}")
    check("upgrade authority", authority, pin["upgrade_authority"])
    check("code sha256", code_hash, pin["code_sha256"])

    cfg_addr, cfg_bump = find_program_address([b"config"], b58decode(pin["program_id"]))
    print(f"config PDA: {cfg_addr} (bump {cfg_bump})")
    cfg, _ = rpc.account(cfg_addr)
    if cfg is None:
        print("LIVECHECK FAILED: Config account not found")
        return 1
    parsed = parse_config_account(base64.b64decode(cfg["data"][0]))
    print(f"config parsed: {parsed}")
    check("config identity authority", parsed["identity_authority"], pin["identity_authority"])
    check("config fee recipient", parsed["fee_recipient"], pin["fee_recipient"])
    check("config rotation authority", parsed["rotation_authority"], pin["rotation_authority"])
    check("config bump", parsed["bump"], cfg_bump)

    if failures:
        print(f"LIVECHECK FAILED: {failures}")
        return 1
    print("LIVECHECK PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

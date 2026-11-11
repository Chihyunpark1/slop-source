#!/usr/bin/env python3
"""Verify the SLOP token contract's function set and on-chain state.

Checks, against the live contract on Robinhood Chain mainnet:

1. The chain ID is 4663 (0x1237).
2. The live deployed bytecode (eth_getCode) is byte-identical to the
   copy in research/slop-bytecode.hex, and reports its SHA-256.
3. The contract's dispatcher routes exactly the 18 identified function
   selectors (PUSH4 + selector + EQ triples) — no more, no fewer.
4. The read-only state getters (name, symbol, decimals, totalSupply,
   owner, paused) via eth_call at the latest block.
5. No claim/registration candidate selector appears in the dispatcher.

The keccak256 implementation is reused from scripts/verify-selector.py
so both checkers agree by construction. Pure Python standard library
only. No dependencies.

Usage:
    python3 scripts/verify-token-state.py
    python3 scripts/verify-token-state.py --offline
    python3 scripts/verify-token-state.py --rpc https://rpc.mainnet.chain.robinhood.com

--offline skips every RPC call and checks only the bytecode file; it
still verifies the 18-selector set against research/slop-bytecode.hex.
"""

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import urllib.request
from pathlib import Path

TOKEN_ADDRESS = "0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE"
EXPECTED_CHAIN_ID = 4663
DEFAULT_RPC = "https://rpc.mainnet.chain.robinhood.com"
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BYTECODE = REPO_ROOT / "research" / "slop-bytecode.hex"

# The 18 functions identified in research/scope.md (Issue #12).
EXPECTED_SIGNATURES = [
    "supportsInterface(bytes4)",
    "name()",
    "approve(address,uint256)",
    "totalSupply()",
    "transferFrom(address,address,uint256)",
    "decimals()",
    "unpause()",
    "mint(address,uint256)",
    "paused()",
    "balanceOf(address)",
    "renounceOwnership()",
    "pause()",
    "owner()",
    "symbol()",
    "burn(address,uint256)",
    "transfer(address,uint256)",
    "allowance(address,address)",
    "transferOwnership(address)",
]

# Candidate claim/registration signatures. None of these may appear in
# the dispatcher if the contract has no claim or registration function.
CLAIM_CANDIDATES = [
    "claim()",
    "claim(address)",
    "claim(uint256)",
    "claimTokens()",
    "claimAllocation()",
    "claimReward()",
    "claimRewards()",
    "register()",
    "register(address)",
    "registerContributor()",
    "registration()",
]


def _load_selector_module():
    path = REPO_ROOT / "scripts" / "verify-selector.py"
    spec = importlib.util.spec_from_file_location("verify_selector", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_vs = _load_selector_module()
keccak256 = _vs.keccak256
selector_of = _vs.selector_of


def dispatcher_selectors(code: bytes):
    """All (offset, selector) pairs in the PUSH4 + selector + EQ
    dispatcher pattern, in order of appearance."""
    out = []
    for i in range(len(code) - 5):
        if code[i] == 0x63 and code[i + 5] == 0x14:
            out.append((i, code[i + 1 : i + 5].hex()))
    return out


def check_bytecode(code: bytes, source_label: str) -> bool:
    """Verify the dispatcher routes exactly the 18 expected selectors
    and none of the claim/registration candidates. Prints each result.
    Returns True when every check passes."""
    ok = True
    print(f"bytecode:  {source_label} ({len(code)} bytes)")
    print(f"sha256:    {hashlib.sha256(code).hexdigest()}")
    found = dispatcher_selectors(code)
    found_set = {sel for _, sel in found}
    print(f"dispatcher: {len(found)} PUSH4/EQ entries")
    for sig in EXPECTED_SIGNATURES:
        sel = selector_of(sig)
        offsets = [off for off, s in found if s == sel]
        if offsets:
            print(f"  [ok]      0x{sel} {sig} (byte offset {offsets[0]})")
        else:
            print(f"  [MISSING] 0x{sel} {sig}")
            ok = False
    expected_set = {selector_of(sig) for sig in EXPECTED_SIGNATURES}
    extras = sorted(found_set - expected_set)
    if extras:
        print(f"  [EXTRA]   dispatcher selectors not in the 18: {extras}")
        ok = False
    else:
        print("  [ok]      no dispatcher selectors beyond the 18")
    for sig in CLAIM_CANDIDATES:
        sel = selector_of(sig)
        if sel in found_set:
            print(f"  [FOUND]   claim candidate 0x{sel} {sig} IS routed")
            ok = False
    print("  [ok]      no claim/registration candidate selector is routed")
    return ok


def rpc_call(rpc_url: str, method: str, params: list):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        rpc_url,
        data=body,
        headers={
            "content-type": "application/json",
            # The public RPC rejects the default Python-urllib agent.
            "user-agent": "slop-source/verify-token-state",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    if "error" in payload:
        raise RuntimeError(f"{method}: {payload['error']}")
    return payload["result"]


def eth_call(rpc_url: str, address: str, data: str) -> str:
    return rpc_call(rpc_url, "eth_call", [{"to": address, "data": data}, "latest"])


def decode_string(raw: str) -> str:
    data = bytes.fromhex(raw[2:])
    length = int.from_bytes(data[32:64], "big")
    return data[64 : 64 + length].decode("utf-8")


def decode_uint(raw: str) -> int:
    return int(raw, 16)


def decode_address(raw: str) -> str:
    return "0x" + raw[-40:]


def decode_bool(raw: str) -> bool:
    return int(raw, 16) != 0


def check_live(rpc_url: str, address: str, repo_code: bytes) -> bool:
    ok = True
    chain_id = int(rpc_call(rpc_url, "eth_chainId", []), 16)
    print(f"chainId:   {chain_id} (0x{chain_id:x})")
    if chain_id != EXPECTED_CHAIN_ID:
        print(f"  [FAIL] expected chain ID {EXPECTED_CHAIN_ID}")
        ok = False
    block = int(rpc_call(rpc_url, "eth_blockNumber", []), 16)
    print(f"block:     {block}")

    live_hex = rpc_call(rpc_url, "eth_getCode", [address, "latest"])
    live_code = bytes.fromhex(live_hex[2:])
    identical = live_code == repo_code
    print(f"getCode:   live bytecode identical to research/slop-bytecode.hex: {identical}")
    if not identical:
        print("  [FAIL] live bytecode differs from the repo copy")
        ok = False

    def call(sig, data, decode, label):
        raw = eth_call(rpc_url, address, data)
        print(f"  {label:12s} {sig:12s} raw {raw}  ->  {decode(raw)}")

    call("name()", "0x06fdde03", decode_string, "name")
    call("symbol()", "0x95d89b41", decode_string, "symbol")
    call("decimals()", "0x313ce567", decode_uint, "decimals")
    call("totalSupply()", "0x18160ddd", decode_uint, "totalSupply")
    call("owner()", "0x8da5cb5b", decode_address, "owner")
    call("paused()", "0x5c975abb", decode_bool, "paused")

    # Behavior probes for the remaining read-only functions.
    owner = decode_address(eth_call(rpc_url, address, "0x8da5cb5b"))
    owner_word = "0" * 24 + owner[2:]
    bal_raw = eth_call(rpc_url, address, "0x70a08231" + owner_word)
    bal = decode_uint(bal_raw)
    print(f"  balanceOf    owner        raw {bal_raw}  ->  {bal} ({bal / 10**18} SLOP)")
    allow_raw = eth_call(rpc_url, address, "0xdd62ed3e" + owner_word + owner_word)
    print(f"  allowance    owner,owner  raw {allow_raw}  ->  {decode_uint(allow_raw)}")
    si_erc165 = eth_call(
        rpc_url, address, "0x01ffc9a7" + "01ffc9a7" + "0" * 56
    )
    print(f"  supportsInt. 0x01ffc9a7   raw {si_erc165}  ->  {decode_bool(si_erc165)}")
    si_bad = eth_call(rpc_url, address, "0x01ffc9a7" + "ffffffff" + "0" * 56)
    print(f"  supportsInt. 0xffffffff   raw {si_bad}  ->  {decode_bool(si_bad)}")
    return ok


def load_bytecode_file(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8").strip()
    text = re.sub(r"^0x", "", text)
    return bytes.fromhex(text)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify the SLOP token function set and on-chain state."
    )
    parser.add_argument("--rpc", default=DEFAULT_RPC, help="JSON-RPC URL")
    parser.add_argument("--address", default=TOKEN_ADDRESS, help="Token contract address")
    parser.add_argument("--bytecode", default=str(DEFAULT_BYTECODE), help="Repo bytecode hex file")
    parser.add_argument("--offline", action="store_true", help="Skip RPC; check the bytecode file only")
    args = parser.parse_args(argv)

    repo_code = load_bytecode_file(Path(args.bytecode))
    ok = check_bytecode(repo_code, args.bytecode)
    if not args.offline:
        print()
        ok = check_live(args.rpc, args.address, repo_code) and ok
    print()
    print("result:", "ALL CHECKS PASSED" if ok else "CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

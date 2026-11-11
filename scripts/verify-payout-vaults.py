#!/usr/bin/env python3
"""Check the live balances of the Solana escrow vaults that the Slop
project registry publishes (GET https://slop.cash/api/v1/projects,
field escrow.deployments).

Read-only: this script only calls getSlot, getAccountInfo and — when a
vault account is not itself a token account — getTokenAccountsByOwner
against the public Solana RPC. It never builds, signs, or sends a
transaction.

Pure Python standard library only. No dependencies.

Usage:
    python3 scripts/verify-payout-vaults.py            # live RPC reads
    python3 scripts/verify-payout-vaults.py --offline  # validate the
        embedded registry records without any network access
"""

import json
import sys
import urllib.request

RPC = "https://api.mainnet-beta.solana.com"

# Solana escrow deployments published in the Slop registry on
# 2026-11-11 (the only three with chain "solana"). The registry also
# publishes two EVM deployments (slopdotcash on Base, thenetwork on
# Robinhood Chain); those are out of scope for this Solana checker.
VAULTS = [
    {
        "project": "eliza",
        "vault": "6NhxSaed6SF3uCAgzQViCZixETGpvxuFzo5eRGiaGM7",
        "owner": "DScqtGwFoDTme2Rzdjpdb2w7CtuKc6Z8KF7hMhbx8ugQ",
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "symbol": "USDC",
        "decimals": 6,
    },
    {
        "project": "hyperliquid-source",
        "vault": "7PJ9FvVQaiNEiGDPDc4dytUinerkhWJq3qFd8bGp5PVK",
        "owner": "DScqtGwFoDTme2Rzdjpdb2w7CtuKc6Z8KF7hMhbx8ugQ",
        "mint": "ABkr21iDncsKabf4CVfXuvkUjCWQkJszGyASL9M7pump",
        "symbol": "EPYH",
        "decimals": 6,
    },
    {
        "project": "pumpfun-source",
        "vault": "DF4GtzFxZ5gMZhbS5ntMaTRFKepcHMqEX2YRHrQ48ahk",
        "owner": "DScqtGwFoDTme2Rzdjpdb2w7CtuKc6Z8KF7hMhbx8ugQ",
        "mint": "35fWL6pdJqpconRZPrawUAQegw1QF3p2tgN7mzhTpump",
        "symbol": "PMUP",
        "decimals": 6,
    },
]

BASE58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def is_base58_address(value):
    return (
        isinstance(value, str)
        and 32 <= len(value) <= 44
        and all(c in BASE58 for c in value)
    )


def format_amount(raw, decimals):
    """Render a base-unit integer string as a decimal string."""
    raw = str(raw)
    if decimals == 0:
        return raw
    raw = raw.rjust(decimals + 1, "0")
    whole, frac = raw[:-decimals], raw[-decimals:]
    frac = frac.rstrip("0")
    return whole + ("." + frac if frac else "")


def check_records():
    problems = []
    for v in VAULTS:
        for field in ("vault", "owner", "mint"):
            if not is_base58_address(v[field]):
                problems.append(f"{v['project']}: {field} is not a base58 address")
        if v["vault"] == v["mint"]:
            problems.append(f"{v['project']}: vault and mint are identical")
    return problems


def rpc(method, params):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        RPC, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.load(resp)
    if "error" in out:
        raise RuntimeError(f"{method}: {out['error']}")
    return out["result"]


def live():
    print(f"slot: {rpc('getSlot', [])}")
    for v in VAULTS:
        print(
            f"\n== {v['project']} vault {v['vault']} "
            f"(asset {v['symbol']} {v['mint']})"
        )
        info = rpc(
            "getAccountInfo",
            [v["vault"], {"encoding": "jsonParsed", "commitment": "finalized"}],
        )
        val = info["value"]
        if val is None:
            print("  vault account: NOT FOUND")
            continue
        print(f"  vault account owner program: {val['owner']}")
        print(f"  vault account lamports: {val['lamports']}")
        data = val.get("data", {})
        parsed = data.get("parsed") if isinstance(data, dict) else None
        if parsed and parsed.get("type") == "account":
            ta = parsed["info"]["tokenAmount"]
            print(f"  vault IS a token account; mint: {parsed['info']['mint']}")
            print(
                f"  token amount: {ta['amount']} "
                f"(ui {ta['uiAmountString']} {v['symbol']})"
            )
            continue
        for label, holder in (("vault", v["vault"]), ("owner", v["owner"])):
            res = rpc(
                "getTokenAccountsByOwner",
                [
                    holder,
                    {"mint": v["mint"]},
                    {"encoding": "jsonParsed", "commitment": "finalized"},
                ],
            )
            accts = res["value"]
            print(
                f"  token accounts owned by {label} ({holder}) "
                f"for mint: {len(accts)}"
            )
            for a in accts:
                ta = a["account"]["data"]["parsed"]["info"]["tokenAmount"]
                print(
                    f"    {a['pubkey']}: {ta['amount']} "
                    f"(ui {ta['uiAmountString']} {v['symbol']})"
                )


def main():
    problems = check_records()
    if problems:
        for p in problems:
            print(f"RECORD ERROR: {p}")
        return 1
    print(f"registry records OK: {len(VAULTS)} Solana vault deployments")
    if "--offline" in sys.argv:
        print("offline mode: no RPC calls made")
        return 0
    live()
    return 0


if __name__ == "__main__":
    sys.exit(main())

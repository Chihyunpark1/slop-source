#!/usr/bin/env python3
"""Verify the live EVM escrow deployments against the published record.

Read-only. For each network in the reviewed factory table of the public
SLOPCASH codebase (contracts/evm/factories.ts at development commit
ced75d782d5836f60d84f46d50604f75a5852438, cross-checked against
contracts/DEPLOY-MAINNET.md and the slop.cash project registry), this
checker confirms, using only public RPC reads:

  - the chain id of the endpoint;
  - the runtime code SHA-256 of the factory proxy, the factory
    implementation, and the vault implementation;
  - the ERC-1967 implementation slot of the factory proxy (the slot
    constant is the one the codebase adapter uses,
    contracts/evm/adapter.ts);
  - the factory's live public state via eth_call: vaultImplementation(),
    registrar(), feeRecipient(), identityAuthority(),
    upgradeAuthority(), bindingDelay();
  - monthlyReserveVersion() read from the vault implementation;
  - that the function selectors used above sit in the dispatcher
    pattern (PUSH4 + selector + EQ) of the live implementation
    bytecode, using the keccak/dispatcher helpers of
    scripts/verify-selector.py.

It never sends a transaction. Transport uses `requests` when it is
installed and falls back to the standard-library `urllib` otherwise;
the keccak/dispatcher helpers are the standard-library ones from
scripts/verify-selector.py.

Usage:
    python3 scripts/verify-evm-deployments.py
    python3 scripts/verify-evm-deployments.py --network robinhood-mainnet
"""

import argparse
import hashlib
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

try:  # preferred transport when available
    import requests
except ImportError:  # standard-library fallback
    requests = None

_HERE = Path(__file__).resolve().parent


def _load_verify_selector():
    spec = importlib.util.spec_from_file_location(
        "verify_selector", _HERE / "verify-selector.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vs = _load_verify_selector()

# --- Published record (see packet research/contracts-evm/evm-contracts-and-deployment.md) ---

FACTORY_PROXY = "0xe51abf8c6dbb3ca6e9ad09f2dc6ef141d7364aab"
FACTORY_IMPLEMENTATION = "0x9f27aec70559d8f4ca1a62398e673a25b1ce3e2f"
VAULT_IMPLEMENTATION = "0x90c46e3e5be35b1048cd69403d1402feed1240d8"
REGISTRAR = "0xd64f35ac87d9a1fb8ebd44e745c24436b606cf60"
IDENTITY_AUTHORITY = "0x31b87d13f9091bc3b8a5cb6f45c8b3cb99ed6d70"
FEE_RECIPIENT = "0x8f77c37d8650776bfe73c9b12b15209ee15d9b86"
UPGRADE_AUTHORITY = "0x2ad20afa352ec70e43a6d0e7794cf305c9cbe35d"

PROXY_CODE_SHA256 = "afb62459ccdd87d344b8bfa367c8dc49586323316bb8a51f1dfbe753336c0509"
FACTORY_IMPL_CODE_SHA256 = "976208154ce5e58f59d826e58273d917adc226109bf95ab4894b9cf144e4a1dd"
VAULT_IMPL_CODE_SHA256 = "155c7ea2fdeeaeccfd6daac64b6105e968c1927092f8761f34090a8b42e15bfc"

# EIP-1967 implementation slot; the same constant the codebase adapter
# uses (contracts/evm/adapter.ts, verifyEvmFactory).
ERC1967_IMPLEMENTATION_SLOT = (
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
)

NETWORKS = [
    {
        "name": "base-mainnet",
        "chain_id": 8453,
        "rpcs": ["https://mainnet.base.org", "https://base-rpc.publicnode.com"],
    },
    {
        "name": "ethereum",
        "chain_id": 1,
        "rpcs": [
            "https://ethereum-rpc.publicnode.com",
            "https://eth.llamarpc.com",
        ],
    },
    {
        "name": "robinhood-mainnet",
        "chain_id": 4663,
        "rpcs": ["https://rpc.mainnet.chain.robinhood.com"],
    },
]

# Selectors that must appear in the dispatcher of each live
# implementation (signature, computed with verify-selector.py keccak).
FACTORY_DISPATCHER_SIGNATURES = [
    "vaultImplementation()",
    "create(bytes32,address,uint8)",
    "upgradeToAndCall(address,bytes)",
]
VAULT_DISPATCHER_SIGNATURES = [
    "monthlyReserveVersion()",
    "deposit(uint128)",
    "pay(bytes32,uint64)",
    "setMonthlyCommitment(uint128,bool)",
]


class Rpc:
    """Minimal read-only JSON-RPC client over the public endpoints."""

    def __init__(self, urls):
        self.urls = urls
        self.url = None

    def call(self, method, params):
        last_error = None
        for url in self.urls:
            for _attempt in range(3):
                try:
                    return self._call_once(url, method, params)
                except Exception as exc:  # retry, then try the next endpoint
                    last_error = exc
        raise RuntimeError(f"all endpoints failed for {method}: {last_error}")

    def _call_once(self, url, method, params):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        headers = {"User-Agent": "slop-source-verify-evm-deployments/1.0"}
        if requests is not None:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            body = resp.json()
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", **headers},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read())
        if "error" in body:
            raise RuntimeError(f"RPC error: {body['error']}")
        self.url = url
        return body["result"]


def word_to_address(word_hex: str) -> str:
    """Low 20 bytes of a 32-byte word, as a lowercase address."""
    return "0x" + word_hex[-40:].lower()


def word_to_int(word_hex: str) -> int:
    return int(word_hex, 16)


class Checker:
    def __init__(self):
        self.failures = 0

    def check(self, label, actual, expected):
        ok = actual == expected
        if not ok:
            self.failures += 1
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {actual}")
        if not ok:
            print(f"       expected: {expected}")
        return ok

    def check_call(self, rpc, label, to, signature, decode, expected):
        data = "0x" + vs.selector_of(signature)
        raw = rpc.call("eth_call", [{"to": to, "data": data}, "latest"])
        return self.check(label, decode(raw), expected)


def check_dispatcher(checker, label, bytecode_hex, signatures):
    for signature in signatures:
        selector = vs.selector_of(signature)
        hits = vs.find_selector(bytecode_hex, selector)
        in_dispatcher = any(in_disp for _, in_disp in hits)
        checker.check(
            f"{label} dispatcher {signature} (0x{selector})",
            "dispatcher" if in_dispatcher else "absent",
            "dispatcher",
        )


def verify_network(checker, network):
    print(f"== {network['name']} (chain id {network['chain_id']}) ==")
    rpc = Rpc(network["rpcs"])
    chain_id = int(rpc.call("eth_chainId", []), 16)
    checker.check("chain id", chain_id, network["chain_id"])
    block = int(rpc.call("eth_blockNumber", []), 16)
    print(f"  block: {block} (via {rpc.url})")

    proxy_code = rpc.call("eth_getCode", [FACTORY_PROXY, "latest"])
    proxy_bytes = bytes.fromhex(proxy_code[2:])
    checker.check(
        "factory proxy runtime sha256",
        hashlib.sha256(proxy_bytes).hexdigest(),
        PROXY_CODE_SHA256,
    )

    slot_word = rpc.call(
        "eth_getStorageAt", [FACTORY_PROXY, ERC1967_IMPLEMENTATION_SLOT, "latest"]
    )
    checker.check(
        "factory proxy ERC-1967 implementation slot",
        word_to_address(slot_word),
        FACTORY_IMPLEMENTATION,
    )

    factory_impl_code = rpc.call("eth_getCode", [FACTORY_IMPLEMENTATION, "latest"])
    factory_impl_bytes = bytes.fromhex(factory_impl_code[2:])
    checker.check(
        "factory implementation runtime sha256",
        hashlib.sha256(factory_impl_bytes).hexdigest(),
        FACTORY_IMPL_CODE_SHA256,
    )

    vault_impl_code = rpc.call("eth_getCode", [VAULT_IMPLEMENTATION, "latest"])
    vault_impl_bytes = bytes.fromhex(vault_impl_code[2:])
    checker.check(
        "vault implementation runtime sha256",
        hashlib.sha256(vault_impl_bytes).hexdigest(),
        VAULT_IMPL_CODE_SHA256,
    )

    checker.check_call(
        rpc, "factory vaultImplementation()", FACTORY_PROXY,
        "vaultImplementation()", word_to_address, VAULT_IMPLEMENTATION,
    )
    checker.check_call(
        rpc, "factory registrar()", FACTORY_PROXY,
        "registrar()", word_to_address, REGISTRAR,
    )
    checker.check_call(
        rpc, "factory feeRecipient()", FACTORY_PROXY,
        "feeRecipient()", word_to_address, FEE_RECIPIENT,
    )
    checker.check_call(
        rpc, "factory identityAuthority()", FACTORY_PROXY,
        "identityAuthority()", word_to_address, IDENTITY_AUTHORITY,
    )
    checker.check_call(
        rpc, "factory upgradeAuthority()", FACTORY_PROXY,
        "upgradeAuthority()", word_to_address, UPGRADE_AUTHORITY,
    )
    checker.check_call(
        rpc, "factory bindingDelay()", FACTORY_PROXY,
        "bindingDelay()", word_to_int, 0,
    )
    checker.check_call(
        rpc, "vault implementation monthlyReserveVersion()", VAULT_IMPLEMENTATION,
        "monthlyReserveVersion()", word_to_int, 2,
    )

    check_dispatcher(
        checker, "factory implementation", factory_impl_code[2:],
        FACTORY_DISPATCHER_SIGNATURES,
    )
    check_dispatcher(
        checker, "vault implementation", vault_impl_code[2:],
        VAULT_DISPATCHER_SIGNATURES,
    )
    print()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify the live EVM escrow deployments (read-only)."
    )
    parser.add_argument(
        "--network",
        choices=[n["name"] for n in NETWORKS],
        help="check only this network",
    )
    args = parser.parse_args(argv)

    checker = Checker()
    for network in NETWORKS:
        if args.network and network["name"] != args.network:
            continue
        verify_network(checker, network)

    if checker.failures:
        print(f"result: {checker.failures} CHECK(S) FAILED")
        return 1
    print("result: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

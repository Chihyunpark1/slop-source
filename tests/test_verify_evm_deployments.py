"""Tests for scripts/verify-evm-deployments.py.

Offline tests only: they pin the checker's own constants and decoding
helpers (selectors computed with the verify-selector.py keccak, the
EIP-1967 slot, word decoding, and the dispatcher scan over synthetic
bytecode). The live network checks themselves run only when the
script is executed directly; they are not exercised here.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-evm-deployments.py"


def _load():
    spec = importlib.util.spec_from_file_location("verify_evm_deployments", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load()


def test_erc1967_slot_is_the_canonical_constant():
    assert mod.ERC1967_IMPLEMENTATION_SLOT == (
        "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    )


def test_selector_pins():
    # Computed with scripts/verify-selector.py (keccak256 of signature).
    assert mod.vs.selector_of("vaultImplementation()") == "bba48a90"
    assert mod.vs.selector_of("monthlyReserveVersion()") == "a763e864"
    assert mod.vs.selector_of("create(bytes32,address,uint8)") == "9a668156"
    assert mod.vs.selector_of("upgradeToAndCall(address,bytes)") == "4f1ef286"
    assert mod.vs.selector_of("deposit(uint128)") == "54469aea"
    assert mod.vs.selector_of("pay(bytes32,uint64)") == "cbcf057d"


def test_word_to_address_takes_low_20_bytes():
    word = "0x" + "00" * 12 + "9f27aec70559d8f4ca1a62398e673a25b1ce3e2f"
    assert mod.word_to_address(word) == "0x9f27aec70559d8f4ca1a62398e673a25b1ce3e2f"


def test_word_to_int():
    assert mod.word_to_int("0x" + "00" * 31 + "02") == 2
    assert mod.word_to_int("0x" + "00" * 32) == 0


def test_dispatcher_signatures_are_routed_in_synthetic_bytecode():
    # Synthetic runtime: PUSH4 <selector> EQ repeated per signature.
    signatures = mod.FACTORY_DISPATCHER_SIGNATURES + mod.VAULT_DISPATCHER_SIGNATURES
    bytecode = "".join("63" + mod.vs.selector_of(sig) + "14" for sig in signatures)
    for sig in signatures:
        hits = mod.vs.find_selector(bytecode, mod.vs.selector_of(sig))
        assert any(in_disp for _, in_disp in hits), sig


def test_expected_addresses_are_well_formed():
    for value in (
        mod.FACTORY_PROXY,
        mod.FACTORY_IMPLEMENTATION,
        mod.VAULT_IMPLEMENTATION,
        mod.REGISTRAR,
        mod.IDENTITY_AUTHORITY,
        mod.FEE_RECIPIENT,
        mod.UPGRADE_AUTHORITY,
    ):
        assert value.startswith("0x") and len(value) == 42
        int(value[2:], 16)

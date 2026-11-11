"""Tests for scripts/verify-token-state.py (offline mode).

These tests verify the token-state checker itself against the SLOP
token bytecode in research/slop-bytecode.hex. They do not call the
live chain: the script's --offline mode checks only that the bytecode
file's dispatcher routes exactly the 18 identified selectors and no
claim/registration candidate. The live state readings the script
performs are documented in research/token/token-contract-state.md.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-token-state.py"


def run_offline():
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--offline"],
        capture_output=True,
        text=True,
    )


def test_offline_checks_pass():
    result = run_offline()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ALL CHECKS PASSED" in result.stdout


def test_dispatcher_has_exactly_the_18():
    result = run_offline()
    assert "dispatcher: 18 PUSH4/EQ entries" in result.stdout
    assert "no dispatcher selectors beyond the 18" in result.stdout
    assert (
        "sha256:    59e56b971f2b6a53b7a469aadf32ff5f48fc1330674fa872757c45518ff9e19e"
        in result.stdout
    )


def test_spot_check_selectors():
    result = run_offline()
    assert "0x40c10f19 mint(address,uint256)" in result.stdout
    assert "0xf2fde38b transferOwnership(address)" in result.stdout
    assert "0x9dc29fac burn(address,uint256)" in result.stdout


def test_no_claim_or_registration_selector():
    result = run_offline()
    assert "no claim/registration candidate selector is routed" in result.stdout
    assert "[FOUND]" not in result.stdout
    assert "[MISSING]" not in result.stdout
    assert "[EXTRA]" not in result.stdout

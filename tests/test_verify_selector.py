"""Tests for scripts/verify-selector.py.

These tests verify the selector checker itself against the SLOP token
bytecode in research/slop-bytecode.hex. They do not test the token;
they test that the checker computes keccak256 selectors correctly and
finds them in deployed bytecode.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-selector.py"
BYTECODE = REPO_ROOT / "research" / "slop-bytecode.hex"


def run(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return result


def test_burn_selector_is_9dc29fac():
    result = run("burn(address,uint256)", "--bytecode", str(BYTECODE))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "selector:  0x9dc29fac" in result.stdout
    assert "keccak256: 9dc29fac0ba6d4fc521c69c2b0c636d612e3343bc39ed934429b8876b0d12cba" in result.stdout
    assert "found at byte offset 182" in result.stdout
    assert "PUSH4 + selector + EQ (dispatcher)" in result.stdout


def test_transfer_selector_is_a9059cbb():
    result = run("transfer(address,uint256)", "--bytecode", str(BYTECODE))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "selector:  0xa9059cbb" in result.stdout
    assert "found at byte offset" in result.stdout


def test_unknown_selector_not_found():
    result = run("foo()", "--bytecode", str(BYTECODE))
    assert result.returncode == 1
    assert "NOT FOUND" in result.stdout


def test_selector_without_bytecode():
    result = run("burn(address,uint256)")
    assert result.returncode == 0
    assert "selector:  0x9dc29fac" in result.stdout

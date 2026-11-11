"""Tests for scripts/verify-payout-vaults.py.

Offline only: these tests validate the registry records embedded in
the checker and its base-unit amount formatting. They make no network
calls; the live RPC reads are exercised by running the script itself.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-payout-vaults.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def load_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("verify_payout_vaults", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_mode_validates_records():
    result = run("--offline")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "registry records OK: 3 Solana vault deployments" in result.stdout


def test_records_are_well_formed():
    module = load_module()
    assert module.check_records() == []
    projects = {v["project"] for v in module.VAULTS}
    assert projects == {"eliza", "hyperliquid-source", "pumpfun-source"}


def test_format_amount():
    module = load_module()
    assert module.format_amount("1000000000", 6) == "1000"
    assert module.format_amount("980000", 6) == "0.98"
    assert module.format_amount("4219710147", 6) == "4219.710147"
    assert module.format_amount("0", 6) == "0"

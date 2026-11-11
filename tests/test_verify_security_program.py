"""Tests for scripts/verify-security-program.py.

These tests verify the registry checker itself against its embedded
offline sample. They do not test the live registry; they test that the
aggregation counts programs correctly and derives the published 75/25
and full-award shares exactly.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-security-program.py"


def run_offline():
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--offline"],
        capture_output=True,
        text=True,
    )


def test_offline_sample_counts():
    result = run_offline()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "projects swept: 3" in result.stdout
    assert "security bounty programs: 2" in result.stdout
    assert "all program checks passed" in result.stdout


def test_offline_standard_split_shares_are_exact():
    result = run_offline()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "sample-standard" in result.stdout
    # 10,000 USDC gross at 6 decimals under the 75/25 split.
    assert "derived shares: researcher 7500000000, slop 2500000000" in result.stdout


def test_offline_full_award_split_pays_researcher_everything():
    result = run_offline()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "sample-full-award" in result.stdout
    assert "derived shares: researcher 1000000, slop 0" in result.stdout

"""Tests for scripts/verify-identity-profile.py.

These tests cover only the offline node-ID decoder: they do not test
slop.cash, and they make no network requests. They check that the
decoder accepts exactly the canonical node-ID forms GitHub emits —
the legacy base64 `04:User<id>` form and the current `U_` MessagePack
`[0, id]` form — and rejects other spellings of the same ID.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-identity-profile.py"


def run(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return result


def test_current_form_decodes_to_numeric_id():
    # The node ID published for the packet author's own directory
    # record; its avatar URL carries u/341532112.
    result = run("--offline", "U_kgDOFFtd0A")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "user id:   341532112" in result.stdout
    assert "result: OK" in result.stdout


def test_legacy_form_decodes_to_numeric_id():
    # base64("04:User123") — the legacy node-ID form.
    result = run("--offline", "MDQ6VXNlcjEyMw==")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "user id:   123" in result.stdout


def test_uint64_spelling_of_a_small_id_is_rejected():
    # [0, 123] encoded with a uint64 marker is a byte string GitHub
    # never emits for this ID, so it must not name the actor.
    result = run("--offline", "U_kgDPAAAAAAAAAHs")
    assert result.returncode == 1
    assert "INVALID" in result.stdout


def test_garbage_node_id_is_rejected():
    result = run("--offline", "U_!!bogus")
    assert result.returncode == 1
    assert "INVALID" in result.stdout

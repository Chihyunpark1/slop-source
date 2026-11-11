"""Tests for scripts/notification-kind-census.py.

These tests verify the census tool itself against a small synthetic
slopdotcash tree built in a temporary directory. They do not test the
real SLOPCASH codebase; they test that the tool parses the migration
CHECK chain, the writer functions, and the presentation registry, and
that it flags a broken chain.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "notification-kind-census.py"

BASE_KINDS = "'application_approved', 'project_revision', 'wallet_changed'"


def write_tree(root: Path, second_kinds: str) -> None:
    (root / "migrations").mkdir(parents=True)
    (root / "migrations" / "0001_notifications.sql").write_text(
        "CREATE TABLE notifications (\n"
        f"  kind TEXT NOT NULL CHECK (kind IN ({BASE_KINDS}))\n"
        ");\n"
    )
    (root / "migrations" / "0002_more_kinds.sql").write_text(
        "CREATE TABLE notifications (\n"
        f"  kind TEXT NOT NULL CHECK (kind IN ({second_kinds}))\n"
        ");\n"
    )
    events = root / "backend" / "notifications"
    events.mkdir(parents=True)
    (events / "events.ts").write_text(
        "export function notifyWallet<S>(db: S): S {\n"
        "  return db.prepare(`INSERT INTO notifications SELECT 'wallet_changed'`);\n"
        "}\n"
        "export function notifyCase<S>(db: S): S {\n"
        "  return db.prepare(`INSERT INTO notifications SELECT\n"
        "    CASE WHEN x THEN 'security_case' ELSE 'project_revision' END`);\n"
        "}\n"
    )
    lib = root / "src" / "lib"
    lib.mkdir(parents=True)
    (lib / "notifications.ts").write_text(
        "const NOTIFICATION_KINDS = [\n"
        '  "application_approved",\n'
        '  "project_revision",\n'
        '  "wallet_changed",\n'
        '  "security_case",\n'
        '  "derived_only_kind",\n'
        "] as const;\n"
    )


def run(root: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
    )


def test_census_over_fixture_tree(tmp_path):
    write_tree(tmp_path, BASE_KINDS + ", 'security_case'")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    out = result.stdout
    assert "final stored set: 4 kinds" in out
    assert "added ['security_case']" in out
    assert "notifyWallet: ['wallet_changed']" in out
    assert "notifyCase: ['project_revision', 'security_case']" in out
    assert "listed but not storable: ['derived_only_kind']" in out
    assert "storable but not listed: []" in out
    # application_approved is storable and listed, but no fixture writer
    # or direct insert produces it.
    assert "  application_approved" in out
    assert "CENSUS PASSED" in out


def test_census_rejects_a_shrinking_chain(tmp_path):
    write_tree(tmp_path, "'application_approved', 'project_revision'")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "BROKEN CHAIN" in result.stdout
    assert "CENSUS FAILED" in result.stdout


def test_census_requires_a_checkout_argument(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 2
    assert "does not look like a slopdotcash checkout" in result.stdout

"""Tests for scripts/audit-workers.py.

These tests verify the auditor itself against a synthetic workers/
tree built in a temporary directory. They do not test the SLOPCASH
workers; they test that the auditor counts the directories, parses
wrangler.toml values, follows the slopbot-style `export { default }`
re-export hop, and distinguishes an empty cron list from a missing
triggers section. The behavior checked here is the evidence method
used by research/workers/background-workers-audit.md.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "audit-workers.py"

NAMES = [
    "fee-converter", "identity", "notify", "operator-keeper",
    "payment-executor", "payments", "referral-accrual",
    "security-payments", "slopbot", "vetting", "vetting-backup",
    "vetting-flags", "vetting-sandbox",
]


def build_tree(root: Path) -> Path:
    workers = root / "workers"
    for name in NAMES:
        (workers / name).mkdir(parents=True)
    (workers / "verified-policy.ts").write_text("// shared module\n")
    fee = workers / "fee-converter"
    fee.joinpath("wrangler.toml").write_text(
        'name = "slop-fee-converter"\nmain = "index.ts"\n'
        '[triggers]\ncrons = ["* * * * *"]\n'
        '[[d1_databases]]\nbinding = "FEE_DB"\n'
        'database_name = "x"\ndatabase_id = "y"\n'
    )
    fee.joinpath("index.ts").write_text(
        "export default {\n  async scheduled() {},\n"
        "  async fetch() { return new Response('Not found', { status: 404 }); },\n};\n"
    )
    bot = workers / "slopbot"
    bot.joinpath("wrangler.toml").write_text(
        'name = "slop-slopbot"\nmain = "entrypoint.ts"\n'
        '[triggers]\ncrons = ["*/5 * * * *"]\n'
        '[[queues.producers]]\nbinding = "SLOPBOT_QUEUE"\nqueue = "slopbot-jobs"\n'
        '[[queues.consumers]]\nqueue = "slopbot-jobs"\n'
    )
    bot.joinpath("entrypoint.ts").write_text(
        'export { default } from "./index";\n'
    )
    bot.joinpath("index.ts").write_text(
        "export default {\n  async fetch() {},\n  async scheduled() {},\n"
        "  async queue() {},\n};\n"
    )
    notify = workers / "notify"
    notify.joinpath("wrangler.toml").write_text(
        'name = "slop-notify"\nmain = "index.ts"\n[triggers]\ncrons = []\n'
    )
    sandbox = workers / "vetting-sandbox"
    sandbox.joinpath("wrangler.toml").write_text(
        'name = "slop-vetting-sandbox"\nmain = "index.ts"\n'
    )
    sandbox.joinpath("index.ts").write_text(
        "export default {\n  async fetch() {},\n};\n"
    )
    return root


def run(root: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
    )


def test_full_tree_passes_and_counts(tmp_path):
    result = run(build_tree(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "workers/ directories: 13" in result.stdout
    assert "shared files (not workers): verified-policy.ts" in result.stdout
    assert "directory set equals the 13 names in issue #13: yes" in result.stdout
    assert "result: ALL CHECKS PASSED" in result.stdout


def test_wrangler_values_and_handler_detection(tmp_path):
    result = run(build_tree(tmp_path))
    out = result.stdout
    assert "| fee-converter | slop-fee-converter | index.ts | fetch,scheduled | * * * * * |" in out
    # slopbot's handlers are found through the entrypoint re-export hop.
    assert "| slopbot | slop-slopbot | index.ts | fetch,scheduled,queue | */5 * * * * |" in out
    assert "queues produced: slopbot-jobs" in out
    assert "D1: FEE_DB" in out


def test_empty_crons_differ_from_missing_triggers(tmp_path):
    result = run(build_tree(tmp_path))
    out = result.stdout
    assert "| notify | slop-notify |" in out and "(empty list)" in out
    assert "| vetting-sandbox | slop-vetting-sandbox | index.ts | fetch | (no triggers section) |" in out


def test_missing_directory_fails(tmp_path):
    root = build_tree(tmp_path)
    (root / "workers" / "vetting-flags").rmdir()
    result = run(root)
    assert result.returncode == 1
    assert "result: MISMATCH" in result.stdout

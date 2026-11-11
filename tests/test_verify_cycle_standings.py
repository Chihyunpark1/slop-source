"""Tests for scripts/verify-cycle-standings.py.

These tests verify the checker itself against small local fixtures.
They do not test slop.cash; they test that the checker validates a
points summary, recomputes competition ranks, checks the snapshot
manifest arithmetic, and validates a frozen cycle proposal's calendar
window and review period.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-cycle-standings.py"


def write(tmp_path, name, value):
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


def summary(contributors, points=None):
    rows = [
        {"actor": {"id": actor_id, "login": login}, "total": total}
        for actor_id, login, total in contributors
    ]
    return {
        "ruleVersion": "slop-points-v1",
        "generatedAt": "2026-11-10T11:02:50.351Z",
        "totals": {
            "contributors": len(rows),
            "points": sum(r["total"] for r in rows) if points is None else points,
        },
        "contributors": rows,
    }


def base_args(tmp_path, **overrides):
    files = {
        "--summary": write(
            tmp_path,
            "summary.json",
            summary([("id-b", "beta", 30), ("id-a", "alpha", 30), ("id-c", "gamma", 10)]),
        ),
        "--cycles": write(
            tmp_path,
            "cycles.json",
            {"schemaVersion": "1", "generatedAt": "2026-11-10T11:02:16.110Z", "cycles": []},
        ),
        "--manifest": write(
            tmp_path,
            "manifest.json",
            {
                "format": "slop-leaderboard-parts-v1",
                "bytes": 12,
                "parts": [{"path": "/x", "bytes": 5, "sha256": "a"},
                          {"path": "/y", "bytes": 7, "sha256": "b"}],
            },
        ),
    }
    files.update(overrides)
    args = []
    for flag, path in files.items():
        if path is not None:
            args += [flag, path]
    return args


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_valid_fixtures_pass_and_ties_share_a_rank(tmp_path):
    result = run(*base_args(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "result: ALL CHECKS PASSED" in result.stdout
    # alpha and beta tie at 30: both rank 1, gamma ranks 3.
    assert "#1 alpha — 30 pts" in result.stdout
    assert "#1 beta — 30 pts" in result.stdout
    assert "#3 gamma — 10 pts" in result.stdout


def test_wrong_points_total_fails(tmp_path):
    bad = write(
        tmp_path,
        "bad-summary.json",
        summary([("id-a", "alpha", 30)], points=999),
    )
    result = run(*base_args(tmp_path, **{"--summary": bad}))
    assert result.returncode == 1
    assert "CHECK(S) FAILED" in result.stdout


def test_proposal_window_and_review_period(tmp_path):
    proposal = write(
        tmp_path,
        "proposal.json",
        {
            "projectId": "eliza",
            "cycleId": "2026-09",
            "status": "proposed",
            "approvedAt": None,
            "contributionWindow": {
                "from": "2026-09-01T00:00:00.000Z",
                "to": "2026-10-01T00:00:00.000Z",
            },
            "review": {
                "days": 14,
                "lastMaterialChangeAt": "2026-10-01T05:52:22.205Z",
                "endsAt": "2026-10-15T05:52:22.205Z",
            },
            "sourceSnapshotSha256": "a" * 64,
            "allocations": [],
        },
    )
    result = run(*base_args(tmp_path, **{"--proposal": proposal}))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "frozen proposal eliza 2026-09" in result.stdout

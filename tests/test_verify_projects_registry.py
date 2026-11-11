"""Tests for scripts/verify-projects-registry.py.

These tests verify the registry checker itself against small fixture
snapshots written to a temporary directory. They do not test slop.cash
and never touch the network: the script is run with --snapshot, the
same offline mode used to re-check the evidence in
research/projects/projects-registry-verification.md.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-projects-registry.py"


def detail(project_id, repository, authority_state, receipt_state):
    verified = authority_state == "verified"
    return {
        "schemaVersion": "1",
        "project": {
            "id": project_id,
            "status": "active",
            "listingTier": "community",
            "steward": {
                "kind": "individual",
                "github": {"login": "steward"},
            },
            "authority": {
                "state": authority_state,
                "reason": None if verified else "missing-repository-proof",
                "proof": {"kind": "fixture"} if verified else None,
            },
            "terms": {
                "revision": "2026-01-01.1" if verified else "draft-1",
                "receiptPolicy": {"state": receipt_state},
            },
            "repositories": [{"id": repository}],
            "slopbot": {"automaticClosure": True},
            "reward": {
                "fundingState": "pledged",
                "committedMinor": "0",
                "paymentMode": "disabled",
                "monthlyCapDisplay": "$0",
            },
        },
        "revision": 1,
        "skillsPublished": True,
        "vetting": {"state": "cleared"},
    }


def write_snapshot(root, entries, list_projects, details):
    (root / "details").mkdir(parents=True)
    discovery = {
        "schemaVersion": "1",
        "projects": [
            {"project_id": pid, "repository": repo} for pid, repo in entries
        ],
    }
    (root / "discovery.json").write_text(json.dumps(discovery))
    (root / "list.json").write_text(
        json.dumps(
            {"schemaVersion": "1", "projects": list_projects, "restrictions": []}
        )
    )
    for project_id, record in details.items():
        (root / "details" / f"{project_id}.json").write_text(json.dumps(record))


def base_snapshot(root):
    entries = [("alpha", "owner/alpha"), ("beta", "owner/beta")]
    list_projects = [
        {"id": "alpha", "status": "active"},
        {"id": "beta", "status": "active"},
        {"id": "gamma", "status": "paused"},
    ]
    details = {
        "alpha": detail("alpha", "owner/alpha", "verified", "active"),
        "beta": detail(
            "beta", "owner/beta", "unverified", "pending-authority-activation"
        ),
    }
    write_snapshot(root, entries, list_projects, details)


def run(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--snapshot", str(root)],
        capture_output=True,
        text=True,
    )


def test_consistent_snapshot_passes(tmp_path):
    base_snapshot(tmp_path)
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ALL CROSS-CHECKS PASSED" in result.stdout
    assert "Discovery entries (projects.json): 2" in result.stdout
    assert "authorityState: unverified=1, verified=1" in result.stdout
    assert "receiptPolicyState: active=1, pending-authority-activation=1" in result.stdout
    assert "'gamma'" in result.stdout
    assert "Statuses of those list-only projects: paused=1" in result.stdout


def test_repository_mismatch_is_reported(tmp_path):
    base_snapshot(tmp_path)
    broken = detail("beta", "owner/other", "unverified",
                    "pending-authority-activation")
    (tmp_path / "details" / "beta.json").write_text(json.dumps(broken))
    result = run(tmp_path)
    assert result.returncode == 1
    assert "PROBLEMS" in result.stdout
    assert "beta" in result.stdout and "owner/beta" in result.stdout


def test_restricted_detail_is_a_row_not_a_failure(tmp_path):
    base_snapshot(tmp_path)
    record = {
        "httpStatus": 410,
        "body": {"restriction": {"state": "quarantined"}},
    }
    (tmp_path / "details" / "beta.json").write_text(json.dumps(record))
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "HTTP 410 (quarantined)" in result.stdout
    assert "ALL CROSS-CHECKS PASSED" in result.stdout

#!/usr/bin/env python3
"""Verify the public, live footprint of SLOPCASH admin & operations.

The admin surfaces themselves are session-only, so this checker reads
only what the platform publishes for anyone and reports the operational
outcomes that are visible there:

1. The cleared-project routing list at
   /.well-known/slop/projects.json (schema 1): which projects publish
   skills at all. Per backend/vetting, a project appears there only
   when its vetting clearance allows skill publication.
2. For every routed project, GET /api/v1/projects/<id>: the public
   vetting summary (state and basis), the project status and whether
   skills are published.
3. GET /api/v1/projects: the public `restrictions` array — the
   quarantined or banned projects whose restriction state the platform
   publishes (project id, state, appeal state, start time).

Pure Python standard library only. No dependencies. Read-only GETs.

Usage:
    python3 scripts/verify-admin-ops.py
    python3 scripts/verify-admin-ops.py --base https://slop.cash
"""

import argparse
import json
import sys
import urllib.request
from collections import Counter

DEFAULT_BASE = "https://slop.cash"


def fetch_json(base: str, path: str):
    request = urllib.request.Request(
        base + path,
        headers={"Accept": "application/json", "User-Agent": "slop-source-verify"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def clearance_kind(vetting: dict) -> str:
    """Classify one public vetting summary into its clearance kind.

    Mirrors the labels the admin view derives from the same fields
    (src/AdminVetting.tsx in the public SLOPCASH codebase): a retained
    admission scan names basis "admission"; the migration-0075
    existing-project exemption sets "grandfathered"; an explicit
    owner-approved admission exemption carries an "exemption" object.
    """
    if vetting.get("basis"):
        return f"basis:{vetting['basis']}"
    if vetting.get("grandfathered"):
        return "grandfathered"
    if isinstance(vetting.get("exemption"), dict):
        return f"exemption:{vetting['exemption'].get('kind')}"
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    failures = []

    routing = fetch_json(base, "/.well-known/slop/projects.json")
    if routing.get("schemaVersion") != "1":
        failures.append(f"routing schemaVersion is {routing.get('schemaVersion')!r}, expected '1'")
    routed = routing.get("projects", [])
    routed_ids = sorted(entry["project_id"] for entry in routed)
    print(f"routing list: {len(routed_ids)} projects publish skills")

    listing = fetch_json(base, "/api/v1/projects")
    projects = listing.get("projects", [])
    restrictions = listing.get("restrictions", [])
    print(f"registry list: {len(projects)} projects, {len(restrictions)} public restrictions")
    for item in restrictions:
        print(
            "  restricted: {pid} state={state} appeal={appeal} since={since}".format(
                pid=item.get("projectId") or item.get("project_id") or item.get("id"),
                state=item.get("state"),
                appeal=item.get("appeal"),
                since=item.get("since") or item.get("startedAt") or item.get("startTime"),
            )
        )

    states = Counter()
    kinds = Counter()
    published = Counter()
    statuses = Counter()
    for project_id in routed_ids:
        payload = fetch_json(base, f"/api/v1/projects/{project_id}")
        project = payload.get("project", payload)
        vetting = payload.get("vetting") or project.get("vetting") or {}
        skills_published = payload.get("skillsPublished", project.get("skillsPublished"))
        state = vetting.get("state")
        kind = clearance_kind(vetting)
        states[state] += 1
        kinds[kind] += 1
        published[bool(skills_published)] += 1
        statuses[project.get("status")] += 1
        print(
            f"  {project_id}: status={project.get('status')} "
            f"vetting={state} clearance={kind} skillsPublished={skills_published}"
        )
        if state != "cleared":
            failures.append(f"{project_id}: routed project vetting state is {state!r}, expected 'cleared'")

    print(f"vetting states: {dict(sorted(states.items(), key=lambda kv: str(kv[0])))}")
    print(f"clearance kinds: {dict(sorted(kinds.items()))}")
    print(f"skillsPublished: {dict(published)}")
    print(f"project statuses: {dict(sorted(statuses.items(), key=lambda kv: str(kv[0])))}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("result: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

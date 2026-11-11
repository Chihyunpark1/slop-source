#!/usr/bin/env python3
"""Verify the public Slop project registry against its own live records.

Reads only public, unauthenticated endpoints:

- GET https://slop.cash/.well-known/slop/projects.json   (discovery)
- GET https://slop.cash/api/v1/projects                  (registry list)
- GET https://slop.cash/api/v1/projects/<project_id>     (one record each)

It aggregates the fields the registry publishes for every project —
status, listing tier, steward, authority state and reason, terms
revision, receipt-policy state, funding state, payment mode, vetting
state and whether generated skills are published — and cross-checks
that the discovery file and the per-project records agree with each
other (same project id, same primary repository).

Standard library only. No credentials, no writes, no state changes.

Usage:
    python3 scripts/verify-projects-registry.py
    python3 scripts/verify-projects-registry.py --save-snapshot DIR
    python3 scripts/verify-projects-registry.py --snapshot DIR

With --snapshot DIR the script reads DIR/discovery.json, DIR/list.json
and DIR/details/<project_id>.json instead of the network, so the same
aggregation can be re-run (and tested) offline. A detail file may also
be a restriction record: {"httpStatus": 410, "body": {...}}.
"""

import json
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ORIGIN = "https://slop.cash"
DISCOVERY_URL = f"{ORIGIN}/.well-known/slop/projects.json"
LIST_URL = f"{ORIGIN}/api/v1/projects"
DETAIL_URL = ORIGIN + "/api/v1/projects/{project_id}"
USER_AGENT = "slop-source-registry-check/1.0 (public read-only verification)"


def fetch_json(url):
    """GET a public JSON document. Returns (http_status, parsed_or_none)."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
        except Exception:
            body = None
        return error.code, body


def dig(value, *keys):
    """Nested dict lookup that returns None instead of raising."""
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def detail_fields(detail):
    """The published fields of one project detail body."""
    project = detail.get("project") or {}
    reward = project.get("reward") or {}
    repositories = project.get("repositories")
    first_repository = (
        repositories[0].get("id")
        if isinstance(repositories, list)
        and repositories
        and isinstance(repositories[0], dict)
        else None
    )
    return {
        "id": project.get("id"),
        "status": project.get("status"),
        "listingTier": project.get("listingTier"),
        "stewardLogin": dig(project, "steward", "github", "login"),
        "stewardKind": dig(project, "steward", "kind"),
        "authorityState": dig(project, "authority", "state"),
        "authorityReason": dig(project, "authority", "reason"),
        "authorityProof": dig(project, "authority", "proof"),
        "termsRevision": dig(project, "terms", "revision"),
        "receiptPolicyState": dig(project, "terms", "receiptPolicy", "state"),
        "repository": first_repository,
        "repositoryCount": len(project.get("repositories") or []),
        "fundingState": reward.get("fundingState"),
        "committedMinor": reward.get("committedMinor"),
        "paymentMode": reward.get("paymentMode"),
        "monthlyCapDisplay": reward.get("monthlyCapDisplay"),
        "automaticClosure": dig(project, "slopbot", "automaticClosure"),
        "skillsPublished": detail.get("skillsPublished"),
        "vettingState": dig(detail, "vetting", "state"),
        "revision": detail.get("revision"),
    }


def summarize(discovery, list_body, details):
    """Aggregate the registry. Returns (report_text, problems).

    details maps project_id -> (http_status, body_or_none).
    """
    problems = []
    lines = []
    if discovery.get("schemaVersion") != "1":
        problems.append(
            f"discovery schemaVersion is {discovery.get('schemaVersion')!r}, not '1'"
        )
    entries = discovery.get("projects") or []
    discovery_ids = [entry.get("project_id") for entry in entries]

    rows = []
    counters = {
        "status": Counter(),
        "listingTier": Counter(),
        "authorityState": Counter(),
        "authorityReason": Counter(),
        "termsRevision": Counter(),
        "receiptPolicyState": Counter(),
        "fundingState": Counter(),
        "paymentMode": Counter(),
        "vettingState": Counter(),
        "skillsPublished": Counter(),
        "stewardKind": Counter(),
        "automaticClosure": Counter(),
    }
    funded = []
    verified_authority = []
    for entry in sorted(entries, key=lambda item: item.get("project_id") or ""):
        project_id = entry.get("project_id")
        status_code, body = details.get(project_id, (None, None))
        if status_code == 410:
            restriction = dig(body, "restriction", "state") or "restricted"
            rows.append(
                {
                    "id": project_id,
                    "status": f"HTTP 410 ({restriction})",
                    "repository": entry.get("repository"),
                }
            )
            counters["status"]["http-410"] += 1
            continue
        if status_code != 200 or not isinstance(body, dict):
            problems.append(f"{project_id}: detail HTTP {status_code}")
            continue
        fields = detail_fields(body)
        if fields["id"] != project_id:
            problems.append(
                f"{project_id}: detail record id is {fields['id']!r}"
            )
        if fields["repository"] != entry.get("repository"):
            problems.append(
                f"{project_id}: discovery repository {entry.get('repository')!r}"
                f" != detail repository {fields['repository']!r}"
            )
        for key in counters:
            counters[key][str(fields.get(key))] += 1
        if str(fields["committedMinor"]) not in ("0", "None"):
            funded.append(f"{project_id} (committedMinor={fields['committedMinor']})")
        if fields["authorityState"] == "verified":
            verified_authority.append(project_id)
        rows.append(fields)

    # The list endpoint returns every current manifest; discovery lists
    # only the projects that publish skills. Compare the two id sets.
    list_projects = (list_body or {}).get("projects") or []
    list_ids = [
        dig(item, "project", "id") or item.get("id") for item in list_projects
    ]
    list_ids = [item for item in list_ids if item]
    restrictions = (list_body or {}).get("restrictions") or []
    only_in_list = sorted(set(list_ids) - set(discovery_ids))
    only_in_discovery = sorted(set(discovery_ids) - set(list_ids))
    list_only_status = Counter()
    for item in list_projects:
        manifest = item.get("project") if isinstance(item.get("project"), dict) else item
        if (manifest or {}).get("id") in only_in_list:
            list_only_status[str((manifest or {}).get("status"))] += 1

    lines.append(f"Discovery entries (projects.json): {len(entries)}")
    lines.append(f"Registry list entries (GET /api/v1/projects): {len(list_ids)}")
    lines.append(
        "In the registry list but not in discovery"
        f" (no published skills): {only_in_list or 'none'}"
    )
    lines.append(
        "Statuses of those list-only projects: "
        + ", ".join(
            f"{value}={count}"
            for value, count in sorted(list_only_status.items())
        )
    )
    lines.append(
        f"In discovery but not in the registry list: {only_in_discovery or 'none'}"
    )
    lines.append(
        "Restrictions published by the list endpoint: "
        + (
            ", ".join(
                f"{item.get('projectId')}={item.get('state')}"
                for item in restrictions
            )
            if restrictions
            else "none"
        )
    )
    lines.append("")
    lines.append(
        "| Project | Status | Tier | Authority | Terms | Receipt policy"
        " | Funding | Committed | Payment | Vetting | Skills |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|"
    )
    for row in rows:
        if "fundingState" not in row:
            lines.append(
                f"| {row['id']} | {row['status']} | — | — | — | — | — | —"
                " | — | — | — |"
            )
            continue
        lines.append(
            f"| {row['id']} | {row['status']} | {row['listingTier']}"
            f" | {row['authorityState']} ({row['authorityReason']})"
            f" | {row['termsRevision']} | {row['receiptPolicyState']}"
            f" | {row['fundingState']} | {row['committedMinor']}"
            f" | {row['paymentMode']} | {row['vettingState']}"
            f" | {row['skillsPublished']} |"
        )
    lines.append("")
    lines.append(
        "| Project | Steward | Kind | Repository | Repos | Auto-close"
        " | Pool cap (display) |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for row in rows:
        if "stewardLogin" not in row:
            lines.append(f"| {row['id']} | — | — | {row['repository']} | — | — | — |")
            continue
        lines.append(
            f"| {row['id']} | {row['stewardLogin']} | {row['stewardKind']}"
            f" | {row['repository']} | {row['repositoryCount']}"
            f" | {row['automaticClosure']} | {row['monthlyCapDisplay']} |"
        )
    lines.append("")
    lines.append("Field counts across all detail records:")
    for name, counter in counters.items():
        summary = ", ".join(
            f"{value}={count}" for value, count in sorted(counter.items())
        )
        lines.append(f"- {name}: {summary}")
    lines.append(
        f"Projects with committedMinor other than 0: {funded or 'none'}"
    )
    lines.append(
        f"Projects with authority.state verified: {verified_authority or 'none'}"
    )
    if problems:
        lines.append("")
        lines.append("PROBLEMS:")
        lines.extend(f"- {problem}" for problem in problems)
    else:
        lines.append("")
        lines.append("ALL CROSS-CHECKS PASSED")
    return "\n".join(lines), problems


def load_snapshot(directory):
    root = Path(directory)
    discovery = json.loads((root / "discovery.json").read_text(encoding="utf-8"))
    list_body = json.loads((root / "list.json").read_text(encoding="utf-8"))
    details = {}
    for path in sorted((root / "details").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(record, dict) and "httpStatus" in record:
            details[path.stem] = (record["httpStatus"], record.get("body"))
        else:
            details[path.stem] = (200, record)
    return discovery, list_body, details


def save_snapshot(directory, discovery, list_body, details):
    root = Path(directory)
    (root / "details").mkdir(parents=True, exist_ok=True)
    (root / "discovery.json").write_text(
        json.dumps(discovery, indent=2), encoding="utf-8"
    )
    (root / "list.json").write_text(
        json.dumps(list_body, indent=2), encoding="utf-8"
    )
    for project_id, (status_code, body) in details.items():
        record = body if status_code == 200 else {"httpStatus": status_code, "body": body}
        (root / "details" / f"{project_id}.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )


def main(argv):
    snapshot_dir = None
    save_dir = None
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--snapshot":
            snapshot_dir = args.pop(0)
        elif arg == "--save-snapshot":
            save_dir = args.pop(0)
        else:
            print(f"unknown argument: {arg}", file=sys.stderr)
            return 2
    if snapshot_dir:
        discovery, list_body, details = load_snapshot(snapshot_dir)
    else:
        status, discovery = fetch_json(DISCOVERY_URL)
        if status != 200 or not isinstance(discovery, dict):
            print(f"discovery fetch failed: HTTP {status}")
            return 1
        status, list_body = fetch_json(LIST_URL)
        if status != 200 or not isinstance(list_body, dict):
            print(f"registry list fetch failed: HTTP {status}")
            return 1
        details = {}
        for entry in discovery.get("projects") or []:
            project_id = entry.get("project_id")
            details[project_id] = fetch_json(DETAIL_URL.format(project_id=project_id))
        if save_dir:
            save_snapshot(save_dir, discovery, list_body, details)
    report, problems = summarize(discovery, list_body, details)
    print(report)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

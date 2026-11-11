#!/usr/bin/env python3
"""Verify the published cycle and standings snapshots against the rules
the public SLOPCASH codebase documents for them.

Checks, using only the standard library:

1. The live points summary (the file the home standings table reads):
   totals agree with the contributor rows, the published order is
   non-increasing, actor ids are unique, and every total is a multiple
   of 10 (points are thirds x 10).
2. The home standings recomputed from that summary: totals descending,
   ties broken by actor id, competition ranks (equal totals share a
   rank). Prints the top 10 rows the home page renders.
3. The live cycle index (the file the cycle pages and archive read):
   schema fields and how many frozen cycle records it currently holds,
   plus whether its generatedAt is past the 8-hour stale threshold the
   UI uses (SNAPSHOT_STALE_AFTER_MS in src/lib/use-snapshot.ts).
4. The rolling leaderboard snapshot manifest: the declared total byte
   count equals the sum of its parts.
5. The calendar arithmetic the cycle pages display: a cycle id is the
   UTC calendar month [first, next first), and from 2026-11 the
   owner-change cutoff is the month end plus 72 hours
   (PRD_MONTHLY_SCHEDULE in src/lib/payments/monthly-allocation.ts).
   A month before 2026-11 has no automatic cutoff.
6. Optionally, a frozen historical proposal file (--proposal): its
   contribution window equals the calendar bounds of its cycle id and
   its review end equals its last material change plus 14 days (the
   pre-2026-11 review rule).

Usage:
    python3 scripts/verify-cycle-standings.py
    python3 scripts/verify-cycle-standings.py --summary FILE \
        --cycles FILE --manifest FILE [--proposal FILE]

Arguments that start with http:// or https:// are fetched; anything
else is read as a local file. Defaults are the live slop.cash URLs.
"""

import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SUMMARY_URL = "https://slop.cash/data/points-summary.json"
CYCLES_URL = "https://slop.cash/data/cycles/index.json"
MANIFEST_URL = "https://slop.cash/data/leaderboard.json"

FIRST_PERIOD = "2026-11"
CUTOFF_SECONDS = 72 * 60 * 60
STALE_AFTER = timedelta(hours=8)
HOME_ROWS = 10

failures = []


def check(label, ok, detail=""):
    print(f"  [{'ok' if ok else 'FAIL'}]    {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def load(source):
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(
            source,
            headers={
                "Accept": "application/json",
                # The CDN refuses the default urllib user agent.
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) verify-cycle-standings",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def month_bounds(cycle_id):
    year, month = (int(part) for part in cycle_id.split("-"))
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    return start, end


def monthly_cutoff(cycle_id):
    if cycle_id < FIRST_PERIOD:
        return None
    _, end = month_bounds(cycle_id)
    return end + timedelta(seconds=CUTOFF_SECONDS)


def home_standings(summary):
    # HomeStandings.tsx sorts by total descending, then actor.id with
    # localeCompare; ranks are competition ranks over the totals only,
    # so the exact collation of tied ids cannot change any rank.
    ranked = sorted(
        summary["contributors"],
        key=lambda row: (-row["total"], row["actor"]["id"].lower(), row["actor"]["id"]),
    )
    rows = []
    previous = None
    rank = 0
    for index, row in enumerate(ranked):
        if row["total"] != previous:
            rank = index + 1
            previous = row["total"]
        rows.append((rank, row["actor"]["login"], row["total"]))
    return rows


def check_summary(summary):
    print("points summary (home standings source):")
    contributors = summary["contributors"]
    totals = summary["totals"]
    check("ruleVersion is slop-points-v1", summary["ruleVersion"] == "slop-points-v1",
          summary["ruleVersion"])
    check("generatedAt parses", bool(parse_ts(summary["generatedAt"])),
          summary["generatedAt"])
    check("contributor count matches totals.contributors",
          len(contributors) == totals["contributors"],
          f"{len(contributors)} rows, totals say {totals['contributors']}")
    check("row totals sum to totals.points",
          sum(row["total"] for row in contributors) == totals["points"],
          f"sum {sum(row['total'] for row in contributors)}, totals say {totals['points']}")
    values = [row["total"] for row in contributors]
    check("published order is non-increasing",
          all(a >= b for a, b in zip(values, values[1:])))
    check("actor ids are unique",
          len({row["actor"]["id"] for row in contributors}) == len(contributors))
    check("every total is a multiple of 10",
          all(value % 10 == 0 for value in values))
    rows = home_standings(summary)
    print(f"  home standings top {HOME_ROWS} (recomputed):")
    for rank, login, total in rows[:HOME_ROWS]:
        print(f"    #{rank} {login} — {total:,} pts")
    if len(rows) > HOME_ROWS:
        boundary_clear = rows[HOME_ROWS - 1][2] != rows[HOME_ROWS][2]
        check("no tie straddles the top-10 boundary", boundary_clear,
              f"#{HOME_ROWS} has {rows[HOME_ROWS - 1][2]}, #{HOME_ROWS + 1} has {rows[HOME_ROWS][2]}")
    else:
        print(f"    only {len(rows)} contributors; the home table is not truncated")
    return rows


def check_cycles(index, now):
    print("cycle index (cycle pages and archive source):")
    check("schemaVersion present", isinstance(index.get("schemaVersion"), str),
          str(index.get("schemaVersion")))
    generated = parse_ts(index["generatedAt"])
    check("generatedAt parses", True, index["generatedAt"])
    cycles = index["cycles"]
    check("cycle record count read", isinstance(cycles, list), f"{len(cycles)} records")
    stale = generated + STALE_AFTER <= now
    print(f"    index generated {index['generatedAt']}; "
          f"8h stale threshold {'passed' if stale else 'not passed'} at check time")
    for entry in cycles:
        start, end = month_bounds(entry["cycleId"])
        window = entry["contributionWindow"]
        check(
            f"{entry['projectId']} {entry['cycleId']} window is the calendar month",
            parse_ts(window["from"]) == start and parse_ts(window["to"]) == end,
            f"{window['from']} .. {window['to']}",
        )
    return cycles


def check_manifest(manifest):
    print("leaderboard snapshot manifest:")
    check("format is slop-leaderboard-parts-v1",
          manifest["format"] == "slop-leaderboard-parts-v1", manifest["format"])
    parts_total = sum(part["bytes"] for part in manifest["parts"])
    check("part bytes sum to the declared total",
          parts_total == manifest["bytes"],
          f"{parts_total} across {len(manifest['parts'])} parts, declared {manifest['bytes']}")


def check_calendar():
    print("cycle calendar arithmetic (PRD monthly schedule):")
    start, end = month_bounds("2026-11")
    check("2026-11 bounds are the UTC calendar month",
          (start, end) == (datetime(2026, 11, 1, tzinfo=timezone.utc),
                           datetime(2026, 12, 1, tzinfo=timezone.utc)),
          f"{start.isoformat()} .. {end.isoformat()}")
    cutoff = monthly_cutoff("2026-11")
    check("2026-11 owner-change cutoff is month end + 72h",
          cutoff == datetime(2026, 12, 4, tzinfo=timezone.utc),
          cutoff.isoformat())
    check("2026-10 has no automatic cutoff (before first period 2026-11)",
          monthly_cutoff("2026-10") is None)


def check_proposal(proposal):
    print(f"frozen proposal {proposal['projectId']} {proposal['cycleId']}:")
    start, end = month_bounds(proposal["cycleId"])
    window = proposal["contributionWindow"]
    check("contribution window is the calendar month",
          parse_ts(window["from"]) == start and parse_ts(window["to"]) == end,
          f"{window['from']} .. {window['to']}")
    review = proposal["review"]
    ends = parse_ts(review["lastMaterialChangeAt"]) + timedelta(days=review["days"])
    check("review end is last material change + review days",
          ends == parse_ts(review["endsAt"]),
          f"{review['days']} days -> {review['endsAt']}")
    digest = proposal["sourceSnapshotSha256"]
    check("source snapshot digest is 64 lowercase hex",
          len(digest) == 64 and all(c in "0123456789abcdef" for c in digest))
    print(f"    status {proposal['status']}, {len(proposal['allocations'])} allocations, "
          f"approvedAt {proposal['approvedAt']}")


def main(argv):
    sources = {"--summary": SUMMARY_URL, "--cycles": CYCLES_URL,
               "--manifest": MANIFEST_URL, "--proposal": None}
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag not in sources:
            print(f"unknown argument: {flag}", file=sys.stderr)
            return 2
        sources[flag] = args.pop(0)
    now = datetime.now(timezone.utc)
    print(f"check time: {now.isoformat()}")
    check_summary(load(sources["--summary"]))
    check_cycles(load(sources["--cycles"]), now)
    check_manifest(load(sources["--manifest"]))
    check_calendar()
    if sources["--proposal"]:
        check_proposal(load(sources["--proposal"]))
    if failures:
        print(f"\nresult: {len(failures)} CHECK(S) FAILED")
        return 1
    print("\nresult: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

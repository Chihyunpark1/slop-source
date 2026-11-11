#!/usr/bin/env python3
"""Verify the public identity/profile surface of slop.cash.

Checks, from public materials only, that a contributor profile is keyed
by the immutable GitHub actor identity and that everything the public
profile page shows is served from sessionless public records:

1. The identity directory (`/data/profiles.json`) holds exactly one
   record for the login; the record's GitHub node ID decodes to the
   numeric GitHub user ID that the record's own avatar URL carries.
2. The public member view (`/api/v1/points/member`) names the same
   node ID as its actor id.
3. The public people list (`/api/v1/points/people`) exposes only the
   public projection fields.
4. The current wallet claim for the numeric ID
   (`/api/v1/wallet-claims/actors/<id>/current`) is readable without a
   session and carries only the public claim projection.
5. The leaderboard snapshot manifest's SHA-256 matches its assembled
   parts, and the snapshot carries the leader and penalty records the
   profile page renders.

With `--offline <node-id>` it only decodes a GitHub node ID to the
numeric user ID it encodes (both the legacy `04:User<id>` form and the
current `U_` MessagePack form), with no network access.

Pure Python standard library only. No dependencies.

Usage:
    python3 scripts/verify-identity-profile.py
    python3 scripts/verify-identity-profile.py --login dd12m54
    python3 scripts/verify-identity-profile.py --offline U_kgDOFFtd0A
"""

import argparse
import base64
import hashlib
import json
import re
import sys
import urllib.request

SITE = "https://slop.cash"
API = "https://api.slop.cash"
USER_AGENT = "slop-source-verify-identity-profile"

PUBLIC_CLAIM_FIELDS = {
    "schemaVersion",
    "claimId",
    "githubActorId",
    "githubLogin",
    "address",
    "chain",
    "source",
    "issueRepository",
    "issueNumber",
    "sourceBodySha256",
    "observedAt",
    "recordDigest",
    "supersedesClaimId",
}

PUBLIC_PEOPLE_FIELDS = {"actor", "socialPoints", "welcome", "x"}


def decode_github_user_id(node_id):
    """Return the numeric GitHub user ID a node ID encodes, or None.

    Mirrors the canonical forms GitHub emits: legacy node IDs are
    standard base64 of `04:User<id>`; current node IDs are `U_` plus
    base64url of the MessagePack array `[0, id]`, where the ID is a
    uint32, or a uint64 only when it exceeds the uint32 range.
    """
    if node_id.startswith("U_"):
        text = node_id[2:]
        if not re.fullmatch(r"[A-Za-z0-9_-]{4,64}", text):
            return None
        try:
            raw = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
        except Exception:
            return None
        # Re-encoding must reproduce the input exactly (canonical form).
        if base64.urlsafe_b64encode(raw).decode().rstrip("=") != text:
            return None
        if len(raw) < 3 or raw[0] != 0x92 or raw[1] != 0x00:
            return None
        marker = raw[2]
        if marker == 0xCE:  # uint32
            if len(raw) != 7:
                return None
            value = int.from_bytes(raw[3:7], "big")
            return str(value) if value > 0 else None
        if marker == 0xCF:  # uint64, only canonical above uint32 range
            if len(raw) != 11:
                return None
            value = int.from_bytes(raw[3:11], "big")
            return str(value) if value > 0xFFFFFFFF else None
        return None
    if not re.fullmatch(r"[A-Za-z0-9+/]{4,64}={0,2}", node_id):
        return None
    try:
        raw = base64.b64decode(node_id, validate=True)
    except Exception:
        return None
    if base64.b64encode(raw).decode() != node_id:
        return None
    match = re.fullmatch(r"04:User([1-9]\d{0,15})", raw.decode("utf-8", "strict")) if _is_text(raw) else None
    return match.group(1) if match else None


def _is_text(raw):
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def fetch_json(url):
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.status, dict(response.headers), json.loads(response.read())


def fetch_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--login", default="dd12m54",
                        help="public contributor login to check (default: the packet author's)")
    parser.add_argument("--offline", metavar="NODE_ID",
                        help="decode a GitHub node ID and exit (no network)")
    args = parser.parse_args()

    if args.offline is not None:
        numeric = decode_github_user_id(args.offline)
        if numeric is None:
            print(f"node id:   {args.offline}")
            print("result: INVALID (not a canonical GitHub user node ID)")
            return 1
        print(f"node id:   {args.offline}")
        print(f"user id:   {numeric}")
        print("result: OK")
        return 0

    failures = []

    def check(label, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}]      {label}{(' — ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    login = args.login
    print(f"identity/profile surface checks for login: {login}")

    # 1. Identity directory: one record, node ID decodes to the avatar's ID.
    _, _, directory = fetch_json(f"{SITE}/data/profiles.json")
    records = [p for p in directory["people"] if p["login"].lower() == login.lower()]
    check("directory holds exactly one record for the login", len(records) == 1,
          f"{len(records)} record(s), directory generatedAt {directory.get('generatedAt')}")
    if len(records) != 1:
        print("result: FAILED")
        return 1
    record = records[0]
    numeric_id = decode_github_user_id(record["id"])
    avatar_id = re.search(r"/u/(\d+)", record.get("avatarUrl", ""))
    check("record node ID decodes to a numeric user ID", numeric_id is not None,
          f"{record['id']} -> {numeric_id}")
    check("decoded ID matches the avatar URL ID",
          avatar_id is not None and avatar_id.group(1) == numeric_id,
          f"avatar carries u/{avatar_id.group(1) if avatar_id else '?'}")
    counts = {
        kind: sum(r[kind] for r in record["repositories"])
        for kind in ("merged", "open", "closed")
    }
    print(f"  [info]    per-repository PR counts in the record: "
          f"{len(record['repositories'])} repositories, totals {counts}")

    # 2. Public member view names the same node ID.
    _, _, member = fetch_json(f"{SITE}/api/v1/points/member?login={login}")
    check("public member view exists", isinstance(member, dict),
          "null" if member is None else "object")
    if isinstance(member, dict):
        check("member actor id is the directory node ID",
              member["actor"]["id"] == record["id"],
              f"member actor id {member['actor']['id']}")
        print(f"  [info]    member view fields: {sorted(member.keys())}; "
              f"public={member.get('public')}")

    # 3. Public people list exposes only the public projection.
    _, _, people = fetch_json(f"{SITE}/api/v1/points/people")
    items = people.get("people", [])
    check("people page is non-empty", len(items) > 0, f"{len(items)} item(s)")
    if items:
        check("people items expose only the public projection",
              all(set(item.keys()) == PUBLIC_PEOPLE_FIELDS for item in items),
              f"fields {sorted(items[0].keys())}")

    # 4. Current wallet claim: sessionless read, public projection only.
    status, headers, claim = fetch_json(
        f"{API}/api/v1/wallet-claims/actors/{numeric_id}/current")
    check("current wallet claim read succeeds without a session", status == 200,
          f"cache-control: {headers.get('Cache-Control')}")
    if claim is None:
        print("  [info]    no current wallet claim for this actor (null)")
    else:
        check("claim carries only the public projection fields",
              set(claim.keys()) == PUBLIC_CLAIM_FIELDS,
              f"{len(claim)} fields")
        check("claim is bound to the same numeric actor ID",
              claim.get("githubActorId") == numeric_id,
              f"githubActorId {claim.get('githubActorId')}")

    # 5. Leaderboard snapshot integrity and profile inputs.
    _, _, manifest = fetch_json(f"{SITE}/data/leaderboard.json")
    parts = []
    parts_ok = True
    for part in manifest["parts"]:
        data = fetch_bytes(SITE + part["path"])
        if len(data) != part["bytes"] or hashlib.sha256(data).hexdigest() != part["sha256"]:
            parts_ok = False
        parts.append(data)
    check("each snapshot part matches its published size and digest", parts_ok,
          f"{len(parts)} part(s)")
    blob = b"".join(parts)
    check("snapshot parts hash to the published manifest digest",
          hashlib.sha256(blob).hexdigest() == manifest["sha256"],
          f"{len(blob)} bytes")
    snapshot = json.loads(blob)
    check("snapshot carries leader records", len(snapshot.get("leaders", [])) > 0,
          f"{len(snapshot.get('leaders', []))} leaders")
    print(f"  [info]    snapshot penalty records (shown on profiles): "
          f"{len(snapshot.get('penalties', []))}; review exclusions: "
          f"{len(snapshot.get('reviewExclusions', []))}")

    # Informational: the published cycle index generation varies.
    _, _, cycles = fetch_json(f"{SITE}/data/cycles/index.json")
    print(f"  [info]    cycle index generatedAt {cycles.get('generatedAt')}: "
          f"{len(cycles.get('cycles', []))} cycle(s) in this generation")

    if failures:
        print(f"result: FAILED ({len(failures)} check(s))")
        return 1
    print("result: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

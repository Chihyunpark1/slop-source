#!/usr/bin/env python3
"""Audit the SLOPCASH background workers from a public slopdotcash checkout.

Reconstructs the worker inventory mechanically: it lists the directories
under ``workers/``, parses every checked-in ``wrangler.toml`` with the
standard TOML parser, and detects the handlers each entry module exports
(``fetch`` / ``scheduled`` / ``queue``), plus ``WorkerEntrypoint`` and
Durable Object classes. It compares the directory set against the 13
names listed in SLOP Source issue #13.

Usage:
    python3 scripts/audit-workers.py <path-to-slopdotcash-checkout>

Standard library only. The script reads files; it never calls the
network and never executes any of the audited code.
"""

import re
import sys
import tomllib
from pathlib import Path

# The 13 names as listed in the Target section of issue #13.
EXPECTED = [
    "fee-converter",
    "identity",
    "notify",
    "operator-keeper",
    "payment-executor",
    "payments",
    "referral-accrual",
    "security-payments",
    "slopbot",
    "vetting",
    "vetting-backup",
    "vetting-flags",
    "vetting-sandbox",
]

HANDLER_RE = {
    "fetch": re.compile(r"\basync\s+fetch\s*\(|\bfetch\s*\([^)]*\)\s*[:{]"),
    "scheduled": re.compile(r"\basync\s+scheduled\s*\("),
    "queue": re.compile(r"\basync\s+queue\s*\("),
}
DEFAULT_EXPORT_RE = re.compile(r"export\s+default\s*\{")
REEXPORT_DEFAULT_RE = re.compile(r'export\s*\{\s*default\s*\}\s*from\s*"\./([A-Za-z0-9_-]+)"')
ENTRYPOINT_CLASS_RE = re.compile(r"export\s+class\s+(\w+)\s+extends\s+WorkerEntrypoint")
PLAIN_CLASS_RE = re.compile(r"export\s+class\s+(\w+)")


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_entry(worker_dir, main):
    """Return the entry module path, following one `export { default }` hop."""
    candidates = []
    if main:
        candidates.append(worker_dir / main)
    candidates += [worker_dir / "index.ts", worker_dir / "entrypoint.ts"]
    for cand in candidates:
        if cand.is_file():
            text = read(cand)
            hop = REEXPORT_DEFAULT_RE.search(text)
            if hop:
                target = worker_dir / (hop.group(1) + ".ts")
                if target.is_file():
                    return target
            return cand
    return None


def detect_handlers(entry_path):
    """Detect handlers inside the entry module's default export."""
    if entry_path is None:
        return [], [], []
    text = read(entry_path)
    match = DEFAULT_EXPORT_RE.search(text)
    handlers = []
    if match:
        body = text[match.start():]
        for name, pattern in HANDLER_RE.items():
            if pattern.search(body):
                handlers.append(name)
    entrypoints = ENTRYPOINT_CLASS_RE.findall(text)
    classes = [c for c in PLAIN_CLASS_RE.findall(text) if c not in entrypoints]
    # WorkerEntrypoint classes may also live in a sibling entrypoint.ts.
    sibling = entry_path.parent / "entrypoint.ts"
    if sibling.is_file() and sibling != entry_path:
        entrypoints += ENTRYPOINT_CLASS_RE.findall(read(sibling))
    return handlers, entrypoints, classes


def parse_wrangler(worker_dir):
    path = worker_dir / "wrangler.toml"
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        cfg = tomllib.load(handle)
    queues = cfg.get("queues", {})
    return {
        "name": cfg.get("name"),
        "main": cfg.get("main"),
        "crons": cfg.get("triggers", {}).get("crons"),
        "has_triggers": "triggers" in cfg,
        "d1": [d.get("binding") for d in cfg.get("d1_databases", [])],
        "r2": [b.get("binding") for b in cfg.get("r2_buckets", [])],
        "queue_producers": [q.get("queue") for q in queues.get("producers", [])],
        "queue_consumers": [q.get("queue") for q in queues.get("consumers", [])],
        "services": [s.get("binding") for s in cfg.get("services", [])],
        "durable_objects": [
            b.get("name")
            for b in cfg.get("durable_objects", {}).get("bindings", [])
        ],
        "send_email": [e.get("name") for e in cfg.get("send_email", [])],
        "routes": bool(cfg.get("routes")),
    }


def audit(root):
    workers_dir = root / "workers"
    dirs = sorted(p.name for p in workers_dir.iterdir() if p.is_dir())
    shared = sorted(p.name for p in workers_dir.iterdir() if p.is_file())
    rows = []
    for name in dirs:
        wdir = workers_dir / name
        cfg = parse_wrangler(wdir)
        main = cfg["main"] if cfg else None
        entry = resolve_entry(wdir, main)
        handlers, entrypoints, classes = detect_handlers(entry)
        rows.append({
            "dir": name,
            "config": cfg,
            "entry": entry.name if entry else None,
            "handlers": handlers,
            "entrypoints": entrypoints,
            "classes": classes,
        })
    return dirs, shared, rows


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = Path(argv[1])
    if not (root / "workers").is_dir():
        print(f"error: {root}/workers not found")
        return 2
    dirs, shared, rows = audit(root)

    print(f"workers/ directories: {len(dirs)}")
    print(f"workers/ shared files (not workers): {', '.join(shared)}")
    print()
    header = ("worker", "wrangler name", "entry", "handlers", "crons (checked-in)")
    print("| " + " | ".join(header) + " |")
    print("| " + " | ".join("---" for _ in header) + " |")
    for row in rows:
        cfg = row["config"]
        wname = cfg["name"] if cfg else "(no wrangler.toml)"
        crons = ""
        if cfg is not None:
            if cfg["crons"]:
                crons = ", ".join(cfg["crons"])
            elif cfg["has_triggers"]:
                crons = "(empty list)"
            else:
                crons = "(no triggers section)"
        handlers = ",".join(row["handlers"]) or "(none in a default export)"
        print(f"| {row['dir']} | {wname} | {row['entry'] or '(none)'} "
              f"| {handlers} | {crons} |")
    print()
    for row in rows:
        cfg = row["config"]
        extras = []
        if cfg:
            for key, label in (("d1", "D1"), ("r2", "R2"),
                               ("queue_producers", "queues produced"),
                               ("queue_consumers", "queues consumed"),
                               ("services", "services"),
                               ("durable_objects", "durable objects"),
                               ("send_email", "send_email")):
                if cfg[key]:
                    extras.append(f"{label}: {', '.join(str(v) for v in cfg[key])}")
        if row["entrypoints"]:
            extras.append("WorkerEntrypoint: " + ", ".join(row["entrypoints"]))
        if row["classes"]:
            extras.append("exported classes: " + ", ".join(row["classes"]))
        print(f"- {row['dir']}: " + ("; ".join(extras) if extras else "(no bindings parsed)"))
    print()
    with_cfg = sum(1 for r in rows if r["config"])
    print(f"census: {len(dirs)} worker directories; {with_cfg} with a checked-in "
          f"wrangler.toml; {len(dirs) - with_cfg} without")
    for handler in ("fetch", "scheduled", "queue"):
        count = sum(1 for r in rows if handler in r["handlers"])
        print(f"census: {count} of {len(dirs)} export a {handler} handler")
    print()
    ok = dirs == sorted(EXPECTED)
    print(f"check: directory set equals the 13 names in issue #13: "
          f"{'yes' if ok else 'NO — ' + str(dirs)}")
    print("result: " + ("ALL CHECKS PASSED" if ok else "MISMATCH"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

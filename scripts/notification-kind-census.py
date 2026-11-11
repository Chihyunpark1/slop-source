#!/usr/bin/env python3
"""Census of the SLOPCASH inbox notification kinds and their producers.

Reads a checkout of the public SlopDotCash/slopdotcash repository and
mechanically cross-checks four registries that must agree:

1. The schema chain: every migration that rebuilds the `notifications`
   table widens its `kind` CHECK. The chain must be strictly growing,
   and the last list is the set of kinds a row may store.
2. The writers: the `notify...` functions in
   `backend/notifications/events.ts`, mapped to the kind literals each
   one can insert, plus any direct `INSERT INTO notifications`
   statements elsewhere in the production code.
3. The call sites of every writer, counted across the production tree.
4. The presentation registry: the kind list in
   `src/lib/notifications.ts`, which the inbox API consumer accepts.

The script prints the full census and exits non-zero if the migration
chain is not strictly increasing or a writer emits a kind the final
schema CHECK does not admit.

Usage:
    python3 scripts/notification-kind-census.py <slopdotcash-checkout>

Standard library only. No network access.
"""

import re
import sys
from pathlib import Path

CHECK_RE = re.compile(
    r"kind\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(\s*kind\s+IN\s*\((.*?)\)\s*\)",
    re.DOTALL,
)
# The widening migrations rebuild the table under its exact name
# (alongside a notifications_NNNN_copy staging table with the same
# list); other tables reuse the column name `kind` with unrelated
# value sets, so the CHECK is only read from this table's own body.
TABLE_RE = re.compile(r"CREATE TABLE notifications \((.*?)\n\)[^;\n]*;", re.DOTALL)
QUOTED_RE = re.compile(r"'([a-z0-9_]+)'")
CODE_SUFFIXES = {".ts", ".tsx", ".mjs", ".js"}
CODE_ROOTS = ("src", "backend", "workers")


def migration_chain(root: Path):
    """Return [(migration name, kind set)] for the notifications table."""
    steps = []
    for path in sorted((root / "migrations").glob("*.sql")):
        text = path.read_text()
        for table in TABLE_RE.finditer(text):
            check = CHECK_RE.search(table.group(1))
            if check:
                kinds = set(QUOTED_RE.findall(check.group(1)))
                steps.append((path.name, kinds))
    chain = []
    for name, kinds in steps:
        if chain and chain[-1][1] == kinds:
            continue
        chain.append((name, kinds))
    return chain


def outbox_trigger_clauses(root: Path):
    """The WHEN clause of the security outbox enqueue trigger, per file."""
    found = []
    pattern = re.compile(
        r"CREATE TRIGGER security_notification_enqueue.*?WHEN NEW\.kind (.*?)\n",
        re.DOTALL,
    )
    simple = re.compile(r"WHEN NEW\.kind\s*=\s*('[^']*')")
    for path in sorted((root / "migrations").glob("*.sql")):
        text = path.read_text()
        match = pattern.search(text)
        if match:
            found.append((path.name, "NEW.kind " + match.group(1).strip()))
        elif "security_notification_enqueue" in text:
            single = simple.search(text)
            if single:
                found.append((path.name, "NEW.kind = " + single.group(1)))
    return found


def split_functions(text: str):
    """Split a TypeScript file into (name, body) at top-level exports."""
    parts = re.split(r"(?m)^export ", text)
    functions = []
    for part in parts[1:]:
        head = re.match(r"(?:async )?(function|const) (\w+)", part)
        if head:
            functions.append((head.group(2), part))
    return functions


def writer_kinds(root: Path, final_kinds: set):
    """Map each notify... writer in events.ts to the kinds it can emit."""
    text = (root / "backend/notifications/events.ts").read_text()
    writers = {}
    for name, body in split_functions(text):
        if name.startswith("notify"):
            kinds = sorted(set(QUOTED_RE.findall(body)) & final_kinds)
            writers[name] = kinds
    return writers


def iter_code_files(root: Path):
    for base in CODE_ROOTS:
        for path in sorted((root / base).rglob("*")):
            if path.is_file() and path.suffix in CODE_SUFFIXES:
                if "node_modules" in path.parts:
                    continue
                yield path


def is_test(path: Path) -> bool:
    return ".test." in path.name or ".workflow." in path.name


def direct_inserts(root: Path, final_kinds: set):
    """INSERT INTO notifications statements outside events.ts."""
    hits = []
    needle = re.compile(r"INSERT INTO notifications", re.IGNORECASE)
    events = root / "backend/notifications/events.ts"
    for path in iter_code_files(root):
        if path == events:
            continue
        text = path.read_text()
        for match in needle.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            window = text[match.start():match.start() + 900]
            kinds = sorted(set(QUOTED_RE.findall(window)) & final_kinds)
            hits.append((path.relative_to(root).as_posix(), line, is_test(path), kinds))
    return hits


def call_sites(root: Path, writers):
    """Count call sites per writer outside events.ts (tests separate)."""
    events = root / "backend/notifications/events.ts"
    counts = {name: {"prod": 0, "test": 0, "files": set()} for name in writers}
    for path in iter_code_files(root):
        if path == events:
            continue
        text = path.read_text()
        rel = path.relative_to(root).as_posix()
        for name in writers:
            n = len(re.findall(r"\b" + re.escape(name) + r"\s*\(", text))
            if n:
                bucket = "test" if is_test(path) else "prod"
                counts[name][bucket] += n
                if bucket == "prod":
                    counts[name]["files"].add(rel)
    return counts


def ui_registry(root: Path):
    text = (root / "src/lib/notifications.ts").read_text()
    match = re.search(
        r"const NOTIFICATION_KINDS = \[(.*?)\] as const", text, re.DOTALL
    )
    if not match:
        return None
    return re.findall(r'"([a-z0-9_]+)"', match.group(1))


def occurrences(root: Path, needle: str):
    places = []
    for path in iter_code_files(root):
        text = path.read_text()
        for i, line in enumerate(text.splitlines(), 1):
            if needle in line:
                places.append(
                    (path.relative_to(root).as_posix(), i, is_test(path))
                )
    return places


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = Path(argv[1])
    if not (root / "migrations").is_dir():
        print(f"error: {root} does not look like a slopdotcash checkout")
        return 2

    ok = True
    chain = migration_chain(root)
    print("== Migration chain for the notifications kind CHECK ==")
    previous = set()
    for name, kinds in chain:
        added = sorted(kinds - previous)
        if previous and not previous < kinds:
            ok = False
            print(f"  BROKEN CHAIN at {name}: not a strict superset")
        print(f"  {name}: {len(kinds)} kinds, added {added}")
        previous = kinds
    final_kinds = chain[-1][1] if chain else set()
    print(f"  final stored set: {len(final_kinds)} kinds")

    print("== Security outbox enqueue trigger (per migration) ==")
    for name, clause in outbox_trigger_clauses(root):
        print(f"  {name}: WHEN {clause}")

    writers = writer_kinds(root, final_kinds)
    print(f"== Writers in backend/notifications/events.ts: {len(writers)} ==")
    produced = set()
    for name, kinds in writers.items():
        produced |= set(kinds)
        print(f"  {name}: {kinds}")
    outside = produced - final_kinds
    if outside:
        ok = False
        print(f"  WRITER KINDS OUTSIDE THE SCHEMA CHECK: {sorted(outside)}")

    inserts = direct_inserts(root, final_kinds)
    print("== Direct INSERT INTO notifications outside events.ts ==")
    for rel, line, test, kinds in inserts:
        tag = "test" if test else "prod"
        print(f"  [{tag}] {rel}:{line} kinds {kinds}")
        if not test:
            produced |= set(kinds)

    counts = call_sites(root, writers)
    print("== Writer call sites (production / test) ==")
    for name in writers:
        entry = counts[name]
        files = ", ".join(sorted(entry["files"]))
        print(f"  {name}: prod {entry['prod']} ({files}); test {entry['test']}")

    ui = ui_registry(root)
    print("== Presentation registry src/lib/notifications.ts ==")
    if ui is not None:
        print(f"  {len(ui)} kinds listed")
        print(f"  listed but not storable: {sorted(set(ui) - final_kinds)}")
        print(f"  storable but not listed: {sorted(final_kinds - set(ui))}")

    derived = occurrences(root, "slopbot_appeal_resolved")
    print("== 'slopbot_appeal_resolved' occurrences ==")
    for rel, line, test in derived:
        print(f"  [{'test' if test else 'prod'}] {rel}:{line}")

    print("== Kinds with no production producer at this checkout ==")
    for kind in sorted(final_kinds - produced):
        print(f"  {kind}")

    print("CENSUS " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

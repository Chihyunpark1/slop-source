# Vetting queue — the current pin: a fresh scan is never blocked by a stale pending one (Issue #5)

## Target

The vetting assessment queue in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #5 (Security —
vetting): the schema change in migration
`migrations/0099_vetting_queue_current_pin.sql`; the assessment table
and the rule it replaces in migration
`migrations/0025_community_security_vetting.sql`; the flag snapshot
column from migration `migrations/0060_contributor_flags.sql`; the
queue entry point in `backend/vetting/handler.ts`; the persistence
layer in `backend/vetting/persistence.ts`; and the replacement flow
exercised in `scripts/vetting-scan-service.test.ts`. The later
replacement link — the column that names which pending scan a new one
replaces — arrives in migration 0103 and is a separate mechanism, not
covered here.

## Claim

Migration 0099 changes the vetting queue's duplicate rule from one
pending scan per project revision to one pending scan per exact live
pin: a new scan is refused only when it repeats the project's current
pending assessment — same revision, same integration-branch commit,
same skill-template digest, and the same active flag set — so a fresh
scan of a new commit or template is never blocked by an older scan
still waiting, while an exact re-offer of the scan already queued is
still refused.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The old rule: one pending scan per revision

Migration 0025 creates the `vetting_assessments` table: one row per
scan, carrying the project id, the revision, the manifest and content
digests, the exact integration-branch commit and the content digest of
the skill template inputs to scan, the requester, the request time and
reason, and a state of pending, incomplete, clean, or malicious. A
pending row carries no result; a completed row carries the policy
version, the signed result, its digests, and the completion time, and
the result must report the same commit and template digest the row was
queued with. The same migration adds a unique index over project id
and revision that applies only while a row is pending, with the stated
intent of one queued scan per revision at a time. It also makes the
history append-only: a trigger refuses every delete, and the only
allowed update records the one result of a pending assessment — no
field of the queued scan may change in the process.

Under that rule, a project whose revision 1 scan was still waiting
could not queue another revision 1 scan at all, even after the
integration branch moved to a new commit or the skill template
changed. The waiting scan pinned the revision until it finished.

### 2. What 0099 changes: three statements, no new columns

Migration 0099 holds exactly three statements. It drops the
one-pending-per-revision index, it creates a plain index over project
id named for the queue, and it adds a before-insert trigger that
refuses a duplicate of the current pin. Its header states the reason:
a pending scan of an old commit or template must not block a fresh
scan, duplicate refusal must be enforced in the database — including
during migration rollout, before the new application code starts
serving requests — and superseded assessments stay unchanged in the
permanent audit history. No column is added, removed, or altered, and
no row is touched.

### 3. The pin: revision, commit, template, and the flag set

The trigger fires only on inserts of a pending row. It looks up the
project's current assessment — the row with the highest row id for
that project — and refuses the insert only when that current row is
itself pending and matches the new row on all four parts of the pin:
the same revision, the same commit digest, the same template digest,
and the same flag set. The flag comparison is set equality, not list
equality: it checks both directions of the difference between the two
flag id lists, so the same flags in a different order still count as
the same pin. The migration comments why: older application versions
do not sort the retained flag ids. The flag list itself comes from
migration 0060, which binds each new scan to the exact active flag
set of its project at queue time and freezes that snapshot — the list
can never be edited afterwards.

Any one part differing makes the new scan a different pin, and the
insert proceeds: a new commit, a new template digest, a different
revision, or a different flag set each queue freely beside the older
pending scan.

### 4. Current only: the pin is the latest row, nothing older

The trigger compares the new row against the latest row for the
project only. An older pending scan with the same identity does not
block anything: once a newer scan has been queued, re-offering the
older scan's identity is accepted, because the current pin has moved
on. Likewise, once the latest row is completed, any identity may be
queued again — there is no pending pin left to duplicate. The queue's
read side agrees on what "current" means: the pending-assessments
read returns only the pending row that is also the latest row for its
project, so older pending scans are visible in the per-project history
but never treated as the queued scan.

### 5. The application side: the live pin, the conflict, and the retry

The queue entry point assigns the live pin at queue time: it reads
the integration-branch head commit and the skill template digest from
the live pin service, and the service cannot choose them — a result
for any other commit is refused. A template-only retry keeps the exact
source assignment that was requested, including when a later commit
removes the reported code. The persistence layer's create call
inserts the pending row, and when the call names a scan to replace,
its guard requires that scan to be pending and to be the latest row
for the project — the same "current" definition the trigger uses.
When the database refuses a duplicate, the error message carries the
word UNIQUE, the persistence layer reports a conflict, and the
handler answers 409 with the queued-scan error; the automatic scan
path reports the same outcome as already queued. The migration header
explains why the refusal lives in the database rather than only in
this code path: it has to hold during rollout, before the new code
serves requests.

### 6. What stays: superseded scans are history, never edited

Nothing in 0099 relaxes the append-only history. A superseded pending
scan is not updated, deleted, or resolved by the arrival of its
replacement — it stays pending with its original commit, template, and
flags, and the 0025 triggers still refuse any edit or delete of it.
The replacement is simply a newer row, and the queue's current-pin
read follows the newest one.

## Verification

Replayed the schema locally in a scratch SQLite database: the 105
migration files numbered 0001 through 0099 applied verbatim, in
order, with zero failures, and the foreign-key check came back empty.
At 0098 the old unique index existed and the 0099 trigger did not; a
second pending scan of the same revision with a new commit was refused
by the index, while a pending scan of a different revision was
accepted. After 0099 the old index was gone, the new queue index
existed on project id alone, and the trigger existed. A pending scan
of the same revision with a new commit was then accepted. An exact
re-offer of that scan was refused with the current-pin error, and the
same flag set in a different order was refused as well. A different
template digest, a different revision, and a different flag set were
each accepted. Re-offering an older pending scan's identity while a
newer scan was latest was accepted, confirming the pin checks only
the latest row. Completing that older scan and re-offering its
identity was accepted, confirming no pending pin remains once the
latest row is complete. All superseded rows kept their original
values, and an update or a delete of a stored assessment was refused
by the append-only guards. The query plan for the current-pending
lookup shows the subquery searching through the new queue index. The
project's own scan-service test exercises the same shape at the
application level: a template change while a scan is pending records
a replacement scan with the new template digest and the original
commit, the original row is unchanged, and racing re-offers of either
row are conflicts. To re-run the replay: check out the `development`
branch of the public codebase, apply the migration files numbered
0001 through 0099 in order into an empty SQLite database, seed one
project with two revisions, and run the insert cases above — a second
pending scan of the same revision with a new commit, an exact re-offer
of the current pin, the same flags reordered, a new template, a new
revision, new flags, a re-offer of an older pending identity, and a
re-offer after completing the latest row.

## Notes

The 409 message the handler returns on a conflict still reads as
though the rule were per revision ("this revision already has a
queued scan"), while the database rule it reports is now per pin;
the wording was not updated with the migration. The explicit link
between a replacement scan and the scan it replaces — the column
naming the replaced assessment — arrives in migration 0103, which
also adds its own guard, and is a separate mechanism from the pin
rule documented here. The vetting reinstatement evidence (migration
0031) and the project publication gates are covered in separate
packets.

# Durable security intake — a Slop receipt is stored before screening or GitHub delivery (Issue #5)

## Target

The private security intake in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #5 (Security): the
schema change in migration
`migrations/0101_durable_security_intake.sql`; the security case table
it rebuilds, from migration `migrations/0026_private_security_cases.sql`
with columns added by migrations 0028, 0059, and 0061; the submission
table from migration `migrations/0059_private_security_submissions.sql`;
the intake handler in `backend/security/report-intake.ts`; and the
report read gate in `backend/security/analysis.ts`. The adjacent
program overview in open PR #57 documents the bounty program, the
private report flow, and case access control at program level; it does
not cover the intake tables or this migration. The intake mechanism
builds on migration 0059 (submissions) and migration 0061 (automatic
intake, which added the award gross amount); neither is re-documented
here beyond what 0101 changes.

## Claim

Migration 0101 makes a Slop security receipt durable before any
screening or GitHub delivery happens: when a private report arrives,
the handler stores one intake row, one versioned report object, and
one intake event in the same batch as the submission itself, and all
four records are immutable and permanent from that moment. A case may
now also exist before its GitHub advisory exists — the advisory
reference becomes optional — and a later manual claim can no longer
duplicate a Slop receipt once its advisory is adopted.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The receipt is stored first, in one batch

The intake handler (`backend/security/report-intake.ts`) creates the
durable receipt together with the submission: it appends a submission
event marked as a durable creation, inserts the intake row in state
`queued`, stores the report as version 1 with its object key, SHA-256
digest, and byte count, and appends an intake event recording the
receipt — each insert guarded so it only lands when the submission
row exists. Screening only starts afterwards: a later step moves the
intake to `running`, records the screening provider and model, and
advances the revision by exactly one; finishing writes the screening
outcome (`legitimate`, `needs-information`, `spam`, or `unavailable`)
with a reason and advances the revision by exactly one again. The
receipt therefore precedes screening by construction — there is no
path in the handler that screens a report with no stored receipt —
and the optional GitHub delivery comes later still: the intake view
lets the reporter authorize or revise the report only while the
submission has no advisory yet.

### 2. The intake tables: one receipt, versioned reports, an event log, an access log

Migration 0101 adds five tables. The intake table
(`security_submission_intake`) holds one row per submission (the
submission id is the primary key) and one case per intake (the case
id is unique), with the receipt time, a report version starting at 1,
the screening state, the screening provider and model, the review
decision and reviewer, and a revision starting at 1. A trigger freezes
the receipt: the submission, the case, and the receipt time can never
change, the revision must advance by exactly one, and the report
version may stay or advance by one — anything else is refused. A
review decision is only storable together with the reviewer and the
review time; a decision without either is refused by a check. Deletes
are refused: intakes are permanent.

The report table (`security_intake_reports`) stores one object per
submission and version, keyed by a unique object key, with a 64
hex-character SHA-256 digest and a byte count between 1 and 262,144.
Updates and deletes are refused: reports are immutable versioned
objects. The event table (`security_intake_events`) is a
revision-keyed log — one row per submission and revision — and its
updates and deletes are refused as well. The access log
(`security_intake_access_log`) records every read and write with the
actor and time, and is append-only: updates and deletes are refused.

The fifth table (`security_intake_rate_admissions`) is deliberately
different: it is ephemeral workload state, not history. The handler
admits at most ten in-flight private-report items per reporter —
counting admitted rows plus received-but-unadmitted intakes — and
refuses further work with a rate-limit error beyond that. The table
carries no immutability trigger, so its rows can be deleted once they
have served their purpose.

### 3. The case rebuild: a case may exist before its advisory

Migration 0101 rebuilds the `security_cases` table under the same
name so deferred child references keep resolving, copying every
existing row into the new table and then dropping the copy. The
rebuild changes one rule: the advisory reference
(`advisory_ghsa`) is no longer required. Since migration 0026 every
case had to name a GitHub advisory; after 0101 a case may be stored
with no advisory at all, matching the intake flow where the report
arrives first and the advisory is adopted later.

Everything else in the case table is carried over unchanged. The six
columns added by earlier migrations ride along: the related-party
assessment (migration 0028), the receipt source and receipt evidence
digest (migration 0059), and the award gross amount (migration 0061).
The receipt source gains a third value in 0101, `slop-received`,
beside the earlier `maintainer-attested` and `github-verified` — a
receipt whose time comes from Slop itself. The frozen-receipt trigger
is re-created with the same coverage it gained in 0059: once a case
is verified, the receipt time, the receipt source, the receipt
evidence digest, the frozen policy revision, the terms, the reporter,
the advisory, and the verified state itself can never change. The
award-amount trigger from 0061 also survives: a reserved award amount
cannot change while a reservation row exists for the case. The two
uniqueness indexes survive too — one verified case per advisory, and
one live claim per reporter and advisory.

### 4. A manual claim cannot duplicate an adopted Slop receipt

Migration 0101 adds a trigger on case inserts: a new case naming an
advisory is refused when a Slop submission for the same project and
repository already holds that advisory in state `submitted` or
`receipt-verified` and has a durable intake row. A manual claim or
import that arrives after the Slop receipt therefore cannot create a
second case for the same advisory; the API resolves authorized
replays instead. A submission still in `draft` does not block a
manual claim — only an adopted receipt does — and a different advisory
for the same project is unaffected.

### 5. A stored report is only readable once it is cleared

The read gate in `backend/security/analysis.ts` only exposes a
stored report when the intake's review decision is `forward`, or when
there is no review decision and the screening state is `legitimate`.
The intake handler applies the same condition when it notifies
maintainers about a case. A report that is still queued or running,
flagged as spam, or awaiting information stays unreadable through
this path even though its receipt is durable.

## Verification

To re-check this claim, replay the migrations verbatim in scratch
SQLite and probe the rules. Applying migrations 0001 through 0101
from `SlopDotCash/slopdotcash` at `development` (`6db280ea`) succeeds
with no failures and an empty foreign-key check (128 migration
files). The checks below were run against that replay; each
"refused" outcome is the database rejecting the statement, each
"accepted" outcome is the statement landing.

1. At migration 0100 none of the five intake tables exists, and a
   case without an advisory is refused (the advisory column is
   required). At 0101 all five tables exist, a case without an
   advisory is accepted, and two cases planted at 0100 — one verified,
   one claimed — survive the rebuild with every column unchanged.
2. One intake per submission and one case per intake: a second intake
   for the same submission is refused, a second intake pointing at
   the same case is refused, and an intake for an unknown submission
   is refused.
3. The intake receipt is frozen: changing the case, the receipt time,
   jumping the revision from 1 to 3, or jumping the report version
   from 1 to 3 are each refused; advancing revision 1 to 2 with
   report version 1 to 2 is accepted; a review decision without
   reviewer and time is refused, and with both is accepted; deleting
   the intake is refused.
4. Reports are immutable versioned objects: version 1 and version 2
   with different object keys are accepted; reusing an object key, a
   63-character digest, a non-hex digest, a byte count of 0, and a
   byte count of 262,145 are each refused; updating or deleting a
   stored report is refused.
5. Events are a revision-keyed immutable log: revision 1 and revision
   2 are accepted, a duplicate revision 1 is refused, and updating
   or deleting an event is refused. The access log accepts a read row
   and refuses updates and deletes.
6. The anti-duplicate trigger: with a submitted Slop submission and
   intake holding one advisory for a project and repository, a manual
   case naming that advisory is refused; a manual case naming a
   different advisory is accepted; a draft submission does not block
   a manual claim.
7. The frozen receipt covers the receipt source and digest: changing
   either on a verified case is refused, while changing a
   non-receipt field (the receipt state) is accepted. Changing a
   reserved award amount while a reservation row exists is refused.
8. The rate-admission table is ephemeral: inserting a row and then
   deleting it is accepted, unlike every other intake table.
9. The earlier uniqueness rules still hold: a second verified case
   for the same advisory and a second live claim by the same reporter
   for the same advisory are each refused.

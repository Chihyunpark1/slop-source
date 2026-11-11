# Owner admission exemptions — a human owner decision admits a repository without a passed scan (Issue #5)

## Target

The owner admission exemption in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #5 (Security):
the schema change in migration
`migrations/0102_owner_admission_exemptions.sql`; the grant and
revoke handlers in `backend/vetting/handler.ts`; the grant, revoke,
and clearance paths in `backend/vetting/persistence.ts`; the
clearance generation that includes exemptions in
`backend/projects/cloudflare-persistence.ts`; and the audit tests in
`scripts/vetting-exemptions.test.ts`. The adjacent program overview
in open PR #57 documents the bounty program, the private report flow,
and case access control at program level; it does not cover the
exemption tables or this migration. Open PR #110 documents the
vetting queue pin from migration 0099 — the queue whose assessments
an exemption covers — not the exemption itself. Open PR #61
documents vetting reinstatement evidence, a different path: a
reinstatement reviews malicious findings, while an exemption never
touches them. The fixed grandfathered set from migration 0075 is
described only as the contrast to this mechanism.

## Claim

Migration 0102 lets an administrator record an explicit human owner
decision that admits a normal repository without inventing a passed
scan: one immutable exemption row pins the project, its current
revision, its manifest hash, the repository identity, and the steward
identity, together with the granting administrator, a reason, an
owner decision reference, and the list of assessments it covers,
frozen at grant time. Clearance follows only when every assessment
for the project is in that covered set, so a later assessment, a
steward transfer, a repository change, or a revocation ends the
clearance. An exemption can never override a project restriction or
an unreviewed malicious finding, and neither the grant nor the
revocation can ever be edited or deleted afterwards.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The two tables: one grant, at most one revocation

Migration 0102 adds two tables. The exemption table
(`vetting_admission_exemptions`) holds one row per grant, with an
auto-increment sequence, an id that must start with `vex_` and be
8 to 80 characters long, the project id and revision, the 64
hex-character manifest hash, the repository id and node id, the
steward actor id and node id, the granting administrator's GitHub id
and login, the grant time, a reason of 1 to 1000 characters, a
decision reference of 1 to 500 characters, and the covered
assessment ids as a JSON array. The project and revision must
reference an existing project revision row. One index serves
lookups by project and sequence.

The revocation table (`vetting_admission_exemption_revocations`)
holds at most one row per exemption — the exemption id is its
primary key — with the revoking administrator, the revocation time,
a reason of 1 to 1000 characters, and a decision reference of 1 to
500 characters. Four triggers freeze both tables: updates and
deletes on exemptions are refused as immutable and permanent, and
the same for revocations. A grant or a revocation, once stored, is
history, not state that can be edited away.

### 2. The grant: an admin-only decision, confirmed, against the current revision

The grant endpoint is `POST admin/vetting/exemptions`. It requires
an administrator session, and admin writes must come from this
site's origin. The body must carry exactly five keys — project id,
revision, reason, decision reference, and confirmation — and the
confirmation must be true, with the message "Confirm the explicit
human owner decision." The reason must be 1 to 1000 characters and
the decision reference 1 to 500 characters.

The grant is bound to the project's current revision: the project
must exist, and the requested revision must equal the project's
current revision, or the grant is refused as stale. The manifest
must name exactly one repository — an exemption covers one immutable
repository. The granting administrator must hold current repository
authority: the handler re-reads repository access, and an admin
without verified authority over that repository is refused. The
repository identity read from GitHub must match the manifest, or the
grant is refused as a repository mismatch. The project must be free
of restrictions and not retired — an exemption cannot override a
project restriction — and there must be no unreviewed malicious
finding — an exemption cannot override a malicious finding.

If an unrevoked exemption already exists for the same project,
repository, and steward identity, the grant is replayed: the
endpoint returns the existing exemption with no new row. Otherwise
it stores a new exemption with a `vex_` id and returns it with the
project setup and the fresh clearance.

### 3. The grant write: every guard re-checked in the database

The grant is a single guarded insert, not a handler-side check
followed by a blind write. The insert lands only when the project
row matches the project id, revision, manifest hash, repository id
and node id, and steward actor id and node id read from the
manifest; when no unreviewed malicious assessment exists for the
project; when the enforcement generation — the highest enforcement
row id — still equals the generation the handler read, so a
concurrent restriction or decision aborts the grant; and when no
unrevoked exemption already exists for the same project, repository,
and steward identity. If any guard fails, the insert writes zero
rows and the handler reports the project changed.

The covered assessment list is computed by the database at grant
time: every assessment id for the project, as a JSON array. The
exemption therefore covers exactly the assessments that existed when
the decision was made — no more, no less. The migration header
states this plainly: the exemption is separate from the fixed
migration-0075 set and never records a passed scan. A pending
assessment covered by an exemption stays pending; the exemption
waives the need for a scan result, it does not fabricate one.

### 4. Clearance: cleared only while every assessment is covered

Clearance checks run in a fixed order. An unreviewed malicious
finding bans the project first. A grandfathered project — one
recorded by the frozen migration-0075 set — clears next. Only then
does the exemption path run, and only for a normal admission: it
needs a repository identity and a steward, and it looks up the
latest unrevoked exemption for that project, repository, and steward
whose revision is at or below the revision being cleared.

The covered set is then extended by one narrow rule only: a
persisted automatic retry continues a covered request when it
replaces the previous assessment at the same revision, manifest,
content, and commit, differing only by a released template. The
free-form reason alone never grants coverage — an explicit
investigation requested after the grant cannot inherit the exemption
from its reason text. Clearance is granted only when every
assessment for the project is in the covered set, and the returned
clearance names the exemption: its id, kind
`owner-approved-admission`, grant time, granting administrator, and
repository identity.

That "every assessment" rule is what makes the exemption narrow. A
new assessment requested after the grant is not in the covered set,
so clearance ends until a fresh decision covers it. A steward
transfer ends it too: the same repository under a different steward
cannot inherit the exemption, and a new grant under the new steward
is needed. A repository change ends it the same way. Routine
revisions keep it — a new revision with the same repository and
steward still clears, because the exemption's revision only has to
be at or below the revision being cleared — but the identity it is
pinned to never changes.

### 5. Revocation: one row, replayed, and clearance returns to normal

The revoke endpoint is `POST
admin/vetting/exemptions/<id>/revoke`, again administrator-only and
same-origin. The body must carry exactly reason, decision
reference, and confirmation, with the same length rules and the same
confirmation requirement. The id must match the `vex_` shape, or the
endpoint reports the exemption as not found. A missing exemption is
a 404; an already-revoked exemption is replayed with the stored
revocation and no new row.

The revocation write inserts one row per exemption id, and a second
attempt for the same exemption writes zero rows — the primary key
and the conflict rule allow exactly one revocation. After a
revocation, clearance is computed as if the exemption never
existed: the project returns to its normal state, which for a
project with a pending assessment is queued behind that assessment.
The admin overview lists exemptions with their revocation state, so
both the grant and its ending stay visible. And because the
clearance generation in the projects persistence includes every
exemption with its revocation flag, a grant or a revocation
invalidates any cached clearance — the change takes effect
immediately rather than waiting for a cache to expire.

### 6. What an exemption cannot do

The limits are the point of the mechanism. It cannot override a
project restriction: the grant handler refuses a restricted or
retired project, and the audit tests show two active contributor
flags still quarantine an exempt project and refuse a second grant.
It cannot override a malicious finding: a malicious result
finishing after the grant bans the project, a new grant is refused,
and a malicious result arriving at the grant write itself aborts
the grant with no exemption stored. It cannot waive a scan that has
not happened: with no assessments at all, clearance is unscanned,
not cleared. And it cannot be used to launder a decision: the
reason and decision reference are stored with the grant, the
granting administrator is named, the confirmation is explicit, and
the whole record is immutable and permanent — the audit trail is the
mechanism, not an afterthought.

The contrast with the grandfathered set is instructive. Migration
0075 recorded every project present when it ran, froze that set
forever with a trigger refusing any insert, and grants clearance
without a scan and without any per-project decision. An exemption
is the opposite: a per-project, per-identity, per-revision human
decision, recorded one at a time, revocable, and only as strong as
the assessment list it froze at grant time.

## Verification

To re-check this claim, replay the migrations verbatim in scratch
SQLite and probe the rules. Applying migrations 0001 through 0102
from `SlopDotCash/slopdotcash` at `development` (`6db280ea`) succeeds
with no failures and an empty foreign-key check (128 migration
files). The checks below were run against that replay; each
"refused" outcome is the database rejecting the statement, each
"accepted" outcome is the statement landing, and each "0 rows"
outcome is the guarded insert writing nothing.

1. At migration 0101 neither exemption table exists, and an insert
   is refused as no such table. At 0102 both tables exist, the
   migration holds exactly two table definitions, one index, and
   four triggers, and two cases planted at 0101 survive the
   migration unchanged.
2. The guarded grant write: a grant naming the wrong manifest hash
   writes 0 rows; a valid grant writes 1 row with the covered list
   holding exactly the one assessment that existed at grant time; a
   second grant for the same project, repository, and steward writes
   0 rows while the first is unrevoked.
3. The schema guards on direct inserts: an id not starting with
   `vex_`, an empty reason, a covered list that is not a JSON array,
   and an exemption naming a revision with no project revision row
   are each refused by their own constraint.
4. Grants and revocations are immutable and permanent: updating or
   deleting an exemption is refused, and updating or deleting a
   revocation is refused, each with the trigger's message.
5. Revocation allows exactly one row: the first revocation writes 1
   row and a second writes 0 rows. A grant after the revocation
   writes 1 row again — a revoked predecessor no longer blocks a
   fresh decision.
6. A malicious finding blocks a fresh grant: with an unreviewed
   malicious assessment stored, the guarded grant writes 0 rows.
7. Coverage is frozen at grant time: an assessment created after the
   grant is not in the stored covered list, so the later assessment
   is outside the exemption's coverage.

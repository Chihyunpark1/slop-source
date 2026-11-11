# Vetting reinstatement evidence — a reinstate clears only the exact malicious findings a fresh clean scan reviewed (Issue #1)

## Target

The project reinstatement evidence rule in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #1 (Projects):
the evidence table created by migration
`migrations/0031_project_vetting_reinstatements.sql`, the enforcement
record it attaches to (`migrations/0027_project_enforcement_owner_appeals.sql`,
the `project_enforcements` table), the assessment table it references
(`migrations/0025_community_security_vetting.sql`, `vetting_assessments`),
the moderator handler that builds the evidence
(`backend/projects/handler.ts`, the `reinstate` branch of the
enforcement endpoint), the clearance check that produces it
(`backend/vetting/persistence.ts`, `clearance` with
`forReinstatement`), and the persistence that stores and reads it
(`backend/projects/cloudflare-persistence.ts`, `appendEnforcement`
and `listEnforcements`). The product rule it implements is in
`docs/slop-product-requirements.md`: after confirmed malice,
reinstatement requires a fresh clean scan and a moderator decision,
and stale evidence cannot reinstate a project.

## Claim

A project-moderator reinstatement is only as wide as the fresh clean
scan behind it. The database records, for every `reinstate`
enforcement, the one clean assessment that justified it and the exact
list of malicious assessments that scan reviewed — and the schema
refuses to record a reinstatement unless that clean scan was
requested after every reviewed malicious finding had completed, was
run on the same project revision the enforcement closes, and was
requested at or after the latest quarantine or ban. A later malicious
finding is never waived by an earlier decision: it stays unreviewed,
so the project reads as banned again until a newer clean scan
reviews it. The evidence row itself can never be edited or deleted.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The evidence table pins one clean scan and the findings it reviewed

Migration 0031 creates `project_vetting_reinstatements` with three
columns: `enforcement_id`, the primary key, referencing the
`project_enforcements` row; `assessment_id`, referencing the
`vetting_assessments` row that is the justifying clean scan; and
`malicious_assessment_ids`, a JSON array of the malicious assessment
ids that scan reviewed. The table is strict, and two triggers make
the evidence permanent: any update aborts with "vetting
reinstatement evidence is immutable" and any delete aborts with
"vetting reinstatement evidence is permanent".

### 2. The insert trigger enforces the freshness rule in the database

Before any row is inserted, the trigger checks two things and aborts
with "reinstatement needs a clean scan after each reviewed finding"
if either fails. First, the linked enforcement must be a `reinstate`
action by a `project-moderator` on a `clean` assessment whose
revision equals the enforcement's `before_revision` — the scan must
be of the exact revision being reinstated, not an older one. Second,
every id in the reviewed list must be a `malicious` assessment of the
same project whose completion time predates the clean scan's request
time: the clean scan must have been requested strictly after each
finding it claims to clear. A clean scan requested before a finding
completed cannot waive that finding, and a finding left out of the
list is not waived at all.

### 3. The handler refuses a reinstatement without a qualifying scan

The enforcement handler builds the evidence only on the `reinstate`
action. It asks the vetting clearance for the project with
reinstatement mode on, then fails the request with HTTP 409
`vetting_required` unless all of these hold: the clearance state is
`cleared`, a clean assessment exists, that assessment's revision is
the project's current revision, and the assessment was requested at
or after the latest quarantine or ban record was created. The
"strictly later request" wording appears in the codebase itself: the
scan-reuse helper notes that service bans require a strictly later
request, citing migration 0031. When the checks pass, the handler
stores the clean assessment's id together with the list of malicious
assessment ids the clearance reported as reviewed, and the
persistence layer inserts the enforcement record and the evidence
row in the same batch.

### 4. The reviewed list is exactly the unwaived malicious findings

The clearance check keeps a waived set: every malicious assessment
id already listed in an earlier reinstatement's evidence row for the
project. Its findings are the project's malicious assessments minus
the waived ones. If a finished clean scan exists but any unwaived
malicious finding completed after that scan was requested, the
clearance does not come back cleared — the project still reads as
banned. Only when the clean scan is newer than every unwaived
finding does the clearance return cleared, with the reviewed list
set to those findings' ids, which is what the handler then records.
A new malicious finding therefore re-bans the project until a newer
clean scan reviews it; no earlier decision can cover it. The same
"unreviewed malicious" query is used elsewhere to decide whether any
malicious assessment is still outstanding.

### 5. The reinstatement is narrow by construction

The enforcement record itself constrains the decision: a `reinstate`
action must close with state `clear` and appeal state `granted`, and
only a `project-moderator` acting from the admin panel may record
it — a steward or applicant may only file a
`request_reinstatement`, never decide one. Reinstatement also does
not clear account bans: the product requirements state that project
reinstatement does not clear account bans, and the handler has a
separate `reinstate_accounts` action that names each banned account
individually. The evidence row is read back whenever enforcements
are listed, attached to its enforcement record as the vetting
review, so the justification for every past reinstatement stays
visible in the project's history.

## Verification

I checked the rule three ways, all against the `development` branch
at commit `6db280ea`.

First, I read the four sources named in the Target: the migration
0031 trigger text, the 0027 enforcement-table constraints, the
handler's reinstate branch (the 409 `vetting_required` conditions and
the evidence it stores), and the clearance function (the waived set,
the findings filter, and the reviewed list it returns). The trigger
condition, the handler condition, and the clearance condition all
agree on the same freshness rule, stated in three places with the
same comparison direction.

Second, I replayed the schema locally in a scratch SQLite database:
I applied migrations 0019, 0023, 0025, 0027, and 0031 in order, then
inserted a ban enforcement, a malicious assessment completed at
10:00, and a clean assessment requested at 09:00. Inserting a
reinstatement evidence row naming the 09:00 clean scan and the 10:00
finding was rejected by the trigger; the same insert with a clean
scan requested at 11:00 was accepted. Updating and deleting the
accepted row were both rejected, with the "immutable" and
"permanent" messages from the triggers.

Third, the repo's own API test exercises the same path end to end in
`scripts/project-registry-api.test.ts`: a reinstate attempted with a
stale scan (the integration-branch head had moved) returns 409
`vetting_required`; a reinstate with no fresh scan also returns 409
and leaves zero rows in the evidence table; and a historical
reinstatement appended with a clean assessment id and one reviewed
malicious id is recorded, after which deleting the evidence row
throws "permanent". I did not run the full test suite here; the
above replay confirms the trigger behavior directly.

## Notes

- This packet covers only the vetting-reinstatement evidence
  mechanism. The enforcement table itself (sequence, roles, appeal
  states), the flag-only automatic reinstatement of a paused project,
  and the account-ban reinstatement path are adjacent mechanisms,
  not covered here.
- The public registry test data I checked contains no live
  reinstatement rows to cross-check against; the claim rests on the
  schema, the handler, the clearance logic, and the local replay,
  not on production rows.
- Related open work: PR #42 covers the project registry, publication
  gates, and live risk flags; PR #49 covers admin operator gates.
  Neither documents this evidence table or its freshness rule.

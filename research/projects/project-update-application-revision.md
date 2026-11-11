# Project update applications — a stored update publishes only against its own base revision (Issue #1)

## Target

The project update-application mechanism in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #1 (Projects):
the two columns migration 0039 adds to `project_applications`, the
revision table and its triggers from migration 0019, the
owner-revision handler and the stored-application publication path in
`backend/projects/handler.ts`, the batched revision append in
`backend/projects/cloudflare-persistence.ts`, and the formal model
`formal/models/api/api_project_revision_receipt.qnt` that describes
the same receipt behavior. The product rule it implements is in
`docs/slop-product-requirements.md` (PRD section 4, owner's revision
publication).

## Claim

A project update is an optimistic-concurrency revision: it is stored
as an application carrying the exact base revision it was written
against, and it can publish only while the project still sits at that
revision. Once any other revision lands, the stored update can never
publish — the setup page stops offering it, a direct publish attempt
fails with 409 `stale_revision`, and the owner must make the change
again from the project's settings. When it does publish, the new
manifest is appended as an immutable revision row and the project's
pointer advances by exactly one; the old revision is never overwritten
or deleted.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The application stores its base revision and its reason

Migration 0039 adds two columns to `project_applications`:
`expected_revision`, a positive integer or null, and `change_reason`,
text of 1–1000 characters or null. The migration's own comment states
the rule: updates use the same review queue and retain their
immutable base revision. A first-time application has no expected
revision; an update application carries one. The persistence layer
reads the two columns back into the application object only when
`expected_revision` is present, and the public application view
exposes both fields, so the stored base is visible to the owner and
the admin.

### 2. The revision history is append-only, and the pointer can only follow it

Migration 0019 creates `project_revisions` with project id and
revision as the primary key, the manifest, its 64-character SHA-256, a
mandatory reason of 1–1000 characters, the acting GitHub account, and
a timestamp; the manifest must be valid JSON naming the same project
id. Two triggers make each row permanent: any update aborts with
"project revisions are immutable" and any delete aborts with "project
revisions are permanent". Two more triggers bind the `projects`
pointer to the history: inserting a project row requires a matching
revision row, and updating the pointer requires the revision to be
exactly one more than the old one with a matching revision row — a
direct jump, or a pointer move without its appended revision, aborts.
A project row itself can never be deleted either ("projects are
permanent; pause instead").

### 3. A stored update is offered only while its base is current

The setup listing filters pending applications through a
publishability check: an application without an expected revision is
always publishable, but one with an expected revision is publishable
only while the project's current revision still equals it. The
handler's comment states the consequence plainly: once another
revision is published the stored update can never succeed, so setup
stops offering it and the owner makes the change again from the
project's settings.

### 4. Publication re-checks the base revision and the restriction state

When the owner publishes a stored update, the handler routes it to
the owner-revision publication path with the stored manifest, the
stored expected revision, and the stored change reason (truncated to
500 characters) as the revision reason. That path first compares the
project's current revision with the expected one and fails with HTTP
409 `stale_revision` if they differ — with the stored-application
wording telling the owner the project changed after the update was
saved and to make the change again in settings. It then refuses
restricted projects (409 `project_restricted`), requires authority
from the stored project rather than from the submitted manifest, and
lets the server decide status and listing tier while the owner
supplies only content. Identity, status, listing, steward, authority
and terms stay on the reviewed exception paths, and a stale expected
revision fails with 409 — as the function's own comment states.

### 5. The write is one fenced batch: append, move the pointer, approve — or none of it

The persistence append takes the expected revision, the enforcement
generation the caller read, and optionally the application id. It
computes the next revision as expected plus one and runs three
statements in one batch, all under the same fence: the revision row is
inserted only while the project still sits at the expected revision,
no enforcement record has landed since the caller read the
restrictions, and — when an application id is given — that
application is still pending with the same expected revision; the
project pointer is updated under the identical fence; and the
application is marked approved only if the pointer actually moved
(the batch checks that exactly one row changed). If any fence fails,
nothing is written and the caller reports a conflict. The enforcement
fence matters because a ban or quarantine landing between the owner's
read and the write must not be overtaken by the revision.

### 6. The formal model agrees: a later head cannot replace the receipt

The Quint model `formal/models/api/api_project_revision_receipt.qnt`,
sourced to the same handler and persistence files, models one own
publication, one concurrent publication, and a possible retry over
revisions 1 to 3. Its scenarios require that a reply after a
competing write still returns the committed revision, not the later
head; that an edited draft retried after another writer landed
reports a conflict; and that a competing write before commit refuses
the publication with no committed revision and no reply. The code's
fences implement exactly those three outcomes.

## Verification

I checked the rule three ways, all against the `development` branch
at commit `6db280ea`.

First, I read the sources named in the Target: the migration 0039
columns, the migration 0019 revision table and its four triggers, the
handler's stored-application publication path and owner-revision path
(the 409 `stale_revision` and `project_restricted` checks, the
authority and server-decided fields), and the persistence append (the
three-statement batch and its fences), plus the formal model. The
handler, the persistence fence, and the model all state the same
base-revision rule with the same comparison.

Second, I replayed the schema locally in a scratch SQLite database: I
applied migrations 0019, 0020, 0023, and 0039 in order, seeded a
project at revision 1 with its revision row and a pending update
application carrying `expected_revision` 1, then ran the append
batch's statements. The fresh update inserted revision 2, moved the
pointer to 2, and marked the application approved. A second
application stored against the old base revision 1 was then attempted
with the same statements: all three wrote zero rows, the pointer
stayed at 2, and the application stayed pending — the conflict
outcome. Updating a revision row was rejected with "project revisions
are immutable", deleting one with "project revisions are permanent",
and moving the pointer to revision 3 without an appended revision row
was rejected with "project update requires the next appended
revision".

Third, the repo's own test exercises the same path end to end in
`scripts/project-self-service.test.ts` ("a stored update whose base
revision moved on is not offered for publication"): while its base is
current the stored update is listed for publication; after another
revision is published from settings it disappears from the listing,
and a direct publication returns 409 `stale_revision` with a message
pointing the owner back to settings, while the project's headline
stays the newer published one. I did not run the full test suite here;
the replay above confirms the database behavior directly.

## Notes

- This packet covers only the update-application revision mechanism:
  the stored base revision, the fenced append, and the append-only
  history. The proposal form and its validation (PR #28), the registry
  and publication gates (PR #42), the vault-setup revision checks in
  the same handler, and the enforcement actions that share the
  expected-revision pattern (PR #49) are adjacent mechanisms, not
  covered here.
- The claim rests on the schema, the handler, the persistence batch,
  the formal model, and the local replay, not on production rows; the
  public registry test data I checked contains no live
  update-application rows to cross-check against.
- Related open work: PR #28 covers the project proposal form; PR #42
  covers the registry, publication gates, and live risk flags; PR #49
  covers admin operator gates; PR #61 covers vetting reinstatement
  evidence. None documents the stored update's base-revision fence or
  the revision append.

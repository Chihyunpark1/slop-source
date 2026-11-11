# Banned-account appeals — a banned account appeals as its own journal actor, but the while-clear filing the docs promise fails the schema check (Issue #1)

## Target

The banned-account appeal mechanism in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #1 (Projects):
the enforcement journal as rebuilt by migration
`migrations/0070_banned_account_appeals.sql`, the owner appeal route
and the moderator endpoint that file appeals
(`backend/projects/handler.ts`, the reinstatement-request handler and
the moderator enforcement endpoint), the write that stores them
(`backend/projects/handler.ts`, the enforcement recorder, and
`backend/projects/cloudflare-persistence.ts`, the batch insert), the
decision model that plans them
(`backend/projects/verified-enforcement.ts`, the action planner and
the account-appeal lookup), the fold that reads appeal state
(`backend/projects/enforcement.ts`, the restriction fold and the
account-appeal state read), the project documentation
(`backend/projects/README.md`, the appeals section), and the product
rule in `docs/slop-product-requirements.md` (PRD section 8): appeal
access is preserved for a banned account, including after a project
transfer.

## Claim

A banned account can file its own reinstatement request as a distinct
journal actor — role `banned-account`, source `account-request` —
without being the project steward or the account that listed the
project, and a later release of that account requires such an open
appeal decided by a moderator who did not ban it; but the while-clear
filing the documentation promises cannot be stored as the handler
writes it, because the plan carries the project's current state into
the record and migration 0070's own check rejects any reinstatement
request whose state is clear.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The role exists only for appeals, and the rebuild preserves history

Migration 0070 rebuilds the enforcement journal table to add
`banned-account` to the allowed actor roles, copying every existing
row with its row id into a new table and back. The table check admits
that role only in one shape: the action is `request_reinstatement`,
the decision source is `account-request`, a GitHub actor id and login
are present, and no system issuer is attached. A banned-account row
with an owner-request source, with a ban action, or with no actor id
is refused by the check. The journal's other rules survive the
rebuild unchanged: records form a gapless sequence per project, and
updates and deletes are refused as immutable and permanent.

### 2. Who may file, and when

The owner appeal route takes a project id, a reason, and an evidence
reference, with an optional account scope. With the scope set to
account, the caller must be currently banned by this project or the
request fails with 403; the record is then filed as
`banned-account`. Without an explicit scope, a banned account files
as `banned-account` when the project is clear or a project appeal is
already open; otherwise the steward files as `project-steward` and
the listing account as `project-applicant`, and anyone else fails
with 403. A banned moderator filing at the admin endpoint is treated
the same way. An appeal changes no revision and has no preview, and
an already-open appeal, or a concurrent record, refuses a second one
with 409. The project documentation states the same rule in plain
words: an account named in the current project ban can use the same
route even if it is no longer the owner and did not list the project,
and a banned account files while the project is clear, or while a
project appeal is open and no later confirmed malicious result kept
that project appeal. In other states, a banned steward, applicant, or
moderator files a project appeal instead.

### 3. Filing grants no project authority and no decision

An account appeal is a request only. The decision model refuses a
project reinstatement that rests on an account-only appeal: with the
project clear there is no open project appeal to decide, so the
request fails with 409. The recorder excludes, from the moderators
allowed to decide a reinstatement request, any moderator who banned
the filing account — and the account itself. Only a moderator who did
not place the restriction or the ban may decide it. The documentation
agrees: filing does not lift a restriction or grant project access,
and only a moderator decides the appeal.

### 4. A later release needs the open appeal

The decision model refuses an account release with 409 unless an
appeal is open, and refuses each selected account separately unless
that account has its own open account appeal. It then refuses with
403 unless the deciding moderator is independent of the ban — a
moderator who banned the account, or who is the account, cannot
decide it. The appeal state is read by pairing ban rows and release
rows per account and by looking up the newest banned-account request
after the last decision boundary, so an open account appeal stays
open after a later quarantine and after a later ban that does not
select that account. The release table itself, and the rule that a
project reinstatement no longer lifts account bans, are covered by
the companion packet on maintainer bans; this packet covers only the
appeal side.

### 5. The while-clear filing fails the schema check as planned

The decision model plans a reinstatement request by carrying the
project's current state forward unchanged, and the recorder stores
that planned state in the journal row. The persistence layer inserts
the record exactly as built, with no adjustment. So an account appeal
filed while the project is clear is planned with a clear state — and
migration 0070's table check requires a reinstatement request to
have a state other than clear. The documentation says the appeal can
be filed while the project is clear, the handler and the model both
admit the filing, and the schema refuses the record they would
write. The schema admits the same appeal when the record carries a
non-clear state, so the gate is the state value, not the role: the
while-clear case is the one that cannot be stored.

## Verification

I checked the rule three ways, all against the `development` branch
at commit `6db280ea`.

First, I read the sources named in the Target: the 0070 rebuild and
its table check, the owner appeal route's scope and role branches,
the admin endpoint's banned-account branch, the recorder's
decision-source rewrite and decider exclusion, the persistence
insert, the decision model's request, release, and reinstatement
branches, the fold's appeal-state read, and the project
documentation's appeals section. The handler, the model, and the
documentation agree the while-clear filing is allowed, and the
migration check disagrees about the record it would produce.

Second, I replayed the schema locally in a scratch SQLite database:
I applied migrations 0001 through 0070 verbatim, in order — 128
files, no failures — then built two projects through the journal. On
the first, a signed vetting-service ban followed by a moderator ban
with a maintainer ban row, then a moderator project reinstatement
that left the project clear while the account ban stayed. On that
project, a banned-account reinstatement request carrying a clear
state was rejected by the table check, while the identical request
carrying a banned state was accepted. On the second project, still
restricted with a banned account, a banned-account request with an
owner-request source was rejected, a banned-account request with a
ban action was rejected, a banned-account request with no actor id
was rejected, and a steward's reinstatement request with an
owner-request source was accepted as the control. The 0070 rebuild
itself preserved every journal row with its id and sequence
unchanged.

Third, the repo's own verified model pins the same paths in
`backend/projects/verified-enforcement.ts` (the account-appeal
lookup, the open-appeal requirement for releases, and the
independent-moderator requirement). I did not run the full test
suite here; the replay above confirms the schema behavior directly,
and the handler and model code confirm what state the planned
record would carry.

## Notes

- This packet covers only the banned-account appeal role and its
  filing and decision gates. The maintainer-ban table, the release
  table, and the rule that a project reinstatement no longer lifts
  account bans are covered by the companion packet on maintainer
  bans. The flag-pause and scan-reinstatement triggers that migration
  0070 recreates alongside the rebuild are adjacent mechanisms, not
  covered here.
- The while-clear divergence is a contradiction between the schema
  and the handler plus model plus documentation, established by the
  replay and the code reads above — not a claim about production
  rows; the public registry test data I checked contains no live
  appeal rows to cross-check against. Whether the intended fix is a
  schema exception for account appeals or a planned state that is
  never clear is a maintainer decision, not part of this packet.
- Related open work: PR #92 covers the maintainer-ban table and its
  release rule and mentions in passing that appeals stay open to a
  banned account; PR #49 covers admin operator gates and mentions
  maintainer bans only in passing; PR #42 covers the project
  registry, publication gates, and live risk flags. None documents
  the `banned-account` role, its filing routes, or the release
  gate.

# Project maintainer bans — a ban rides on the moderator's decision and lifts only by a separate account release (Issue #1)

## Target

The project maintainer ban mechanism in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #1 (Projects):
the ban table created by migration
`migrations/0066_project_maintainer_bans.sql`, the release table
created by migration `migrations/0072_account_reinstatements.sql`,
the enforcement journal both attach to
(`migrations/0023_project_enforcements.sql` as rebuilt by 0072,
`project_enforcements`), the moderator handler that records both
(`backend/projects/handler.ts`, the enforcement endpoint), the
persistence that stores them in one batch
(`backend/projects/cloudflare-persistence.ts`, `appendEnforcement`),
the read that decides whether an account is banned
(`backend/projects/account-bans.ts`, `hasParticipationBan`, and
`backend/projects/enforcement.ts`, `activeAccountBans`), and the
product rule in `docs/slop-product-requirements.md` (PRD sections 2
and 8): after confirmed malice a moderator decides whether to
reinstate the project or ban it and its maintainer.

## Claim

A maintainer ban is never a standalone record. It can only be written
as part of a moderator's Ban decision on a signed confirmed-malicious
vetting ban, naming only the accounts the moderator selected from the
evidence, and the ban row itself can never be edited or deleted. The
ban stays in force until a different moderator releases that exact
account with a `reinstate_accounts` decision — a project
reinstatement alone no longer lifts it, even though migration 0066's
header comment still says it does; migration 0072 changed the rule
and the current code and documentation agree on the new one.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The ban table pins one account to one Ban decision

Migration 0066 creates `project_maintainer_bans` with three columns:
`enforcement_id`, referencing the `project_enforcements` row that is
the moderator's Ban decision; `github_id`, the banned account's
immutable GitHub actor id, checked to be a 1-to-20 digit number not
starting with zero; and `github_login`, 1 to 39 characters. The
primary key is the pair of enforcement id and account id, so one
decision can ban several accounts and one account can be banned by
several decisions, and an index on the account id supports the
banned-or-not lookup. Two triggers make each row permanent: any
update aborts with "maintainer bans are immutable" and any delete
aborts with "maintainer bans are permanent".

### 2. The insert trigger allows a ban only on a confirmed-malicious decision

Before any row is inserted, the trigger checks the enforcement row it
attaches to and aborts with "a maintainer ban needs a moderator
decision on a confirmed malicious ban" unless all three hold. First,
the enforcement row must be a `ban` action by a `project-moderator`.
Second, the latest earlier quarantine or ban for the same project
must have been recorded by the `vetting-service` — the signed
service, not a moderator or a flag. Third, the immediately preceding
journal row for the project must have left the project `banned`.
Together these say the moderator's Ban is a decision on a vetting
ban that is already in force, not a first strike of its own. A
moderator-only chain, or a Ban that follows a quarantine that never
became a ban, cannot carry a maintainer ban.

### 3. The handler only bans accounts the moderator selected, in the same write

The enforcement handler refuses to record account bans unless the
decision plan says the decision bans a maintainer — a flag the
verified enforcement model only sets for a Ban that decides
maliciousness — and fails with HTTP 400 `invalid_request`,
"Account bans require a moderator decision on a confirmed malicious
result", otherwise. The accounts come only from the moderator's
selection in the request; current stewardship and the original
application never select accounts automatically, and an empty
selection bans only the project. The handler builds one enforcement
record holding the Ban, the selected maintainer bans, and any account
releases, and the persistence layer inserts the enforcement row, the
ban rows, and the release rows in a single database batch, so the ban
cannot land without its decision record.

### 4. Only a different moderator's release lifts a ban, account by account

Migration 0072 creates `project_account_reinstatements` with three
columns: `enforcement_id`, the `reinstate_accounts` decision that
releases the account; `ban_enforcement_id`, the Ban decision being
released from; and `github_id`. Its primary key is the ban decision
plus the account, with a foreign key back to the exact ban row, so a
release always names the ban it undoes. Before any row is inserted,
the trigger requires a `reinstate_accounts` decision by a
`project-moderator` on the same project, later in the journal than
the ban, by a different moderator than the one who banned the
account, and with no revision attached — and aborts with "account
reinstatement needs an independent moderator decision on its ban"
otherwise. The handler adds its own checks: an empty selection is
refused, and each selected account must have an active ban from this
project, or the request fails with 409 `account_not_banned`. Release
rows are immutable and permanent, like the ban rows.

### 5. A project reinstatement no longer lifts account bans

Migration 0066's header comment says a later reinstatement of the
project lifts the ban. That was the former rule. Migration 0072
states the change in its own comment — "New project reinstatements
do not release accounts implicitly" — and its backfill only preserves
releases already made under the former project-wide rule, converting
each into an explicit release row pointing at the first later project
reinstatement. The project documentation says the same thing in
plain words: "A project reinstatement no longer lifts account bans",
and a moderator who did not ban an account, and is not that account,
uses `reinstate_accounts` to select the accounts cleared by the
evidence, leaving the project restriction and other accounts
unchanged. The banned-or-not read confirms it: it returns banned
whenever a ban row exists with no release row for that ban and
account, and it never consults the project's current state, so a
project reinstatement cannot change its answer.

### 6. What "banned" means when it is read

Two reads agree on the same pairing of ban rows and release rows.
The participation check asks whether a ban row exists for the
account with no matching release row for that ban decision and
account. The enforcement fold pairs bans and releases by the same
ban-decision-plus-account key and keeps only the unreleased ones.
The participation check is enforced wherever a banned account would
start new work: monthly payments refuse with 403 `account_banned`,
"This account cannot change or finalize new monthly awards while
banned"; security submissions refuse with 403
`participation_banned`, "This account cannot start new Slop work.
Existing cases, funded awards and appeals remain available"; award
approval refuses a banned reporter or actor; and the trace API
refuses new contribution runs. The project documentation adds that
a banned maintainer cannot create a project, publish a stored
application, or publish an owner revision, as the actor or as the
named steward, and that the score generator gives a banned account
no contribution or review credit for events at or after its ban
start, while earlier credit stays. What remains open to a banned
account: appeals (including after ownership changes), reading and
withdrawing existing flags, existing cases, and funded awards — and
the ban never erases an approved funded award.

## Verification

I checked the rule three ways, all against the `development` branch
at commit `6db280ea`.

First, I read the sources named in the Target: the 0066 ban table
and its insert trigger, the 0072 release table and its insert
trigger, the handler's Ban and `reinstate_accounts` branches
(including the `bansMaintainer` plan gate and the
`account_not_banned` check), the persistence batch that stores
enforcement, bans, and releases together, the two banned-or-not
reads, and the project documentation's account-ban section. The
trigger condition, the handler condition, and the two reads all
agree on the same rule, and the 0072 comment and the documentation
agree that the 0066 header comment's project-reinstatement sentence
is no longer the rule.

Second, I replayed the schema locally in a scratch SQLite database:
I applied migrations 0001 through 0072 verbatim, in order — 77
files, no failures — then ran three projects through the journal.
On the first, a vetting-service ban followed by a moderator ban
accepted a ban row for one maintainer; a ban row pointing at the
vetting-service row was rejected; updating and deleting the accepted
row were rejected with the "immutable" and "permanent" messages;
and the banned-or-not query returned banned. A release row with no
`reinstate_accounts` decision was rejected. A moderator project
reinstatement (appeal granted) left the query returning banned. A
`reinstate_accounts` decision by a different moderator accepted a
release row, after which the query returned not banned, and updating
and deleting the release row were rejected. On the second project, a
moderator quarantine followed by a moderator ban — no
vetting-service ban behind it — could not carry a ban row. On the
third, a `reinstate_accounts` decision by the same moderator who
banned the account was accepted as a journal row but its release row
was rejected, and the account stayed banned.

Third, the repo's own tests exercise the same paths in
`backend/projects/verified-enforcement.ts` (the model pins
`bansMaintainer` to a Ban that decides maliciousness) and in the
enforcement handler tests. I did not run the full test suite here;
the replay above confirms the trigger behavior directly.

## Notes

- This packet covers only the maintainer-ban table and its release
  table. The enforcement journal itself (sequence, roles, appeal
  states), the vetting-reinstatement evidence table, and the
  flag-only automatic reinstatement are adjacent mechanisms, not
  covered here.
- The claim rests on the schema, the handler, the two reads, the
  documentation, and the local replay, not on production rows; the
  public registry test data I checked contains no live ban rows to
  cross-check against.
- Related open work: PR #42 covers the project registry,
  publication gates, and live risk flags; PR #49 covers admin
  operator gates and mentions maintainer account bans only in
  passing as part of the admin UI; PR #61 covers the
  vetting-reinstatement evidence table. None documents this ban
  table, its insert gate, or the release rule.

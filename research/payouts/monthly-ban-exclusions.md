# Monthly ban exclusions — a banned recipient's award is excluded at funding time (Issue #3)

## Target

The monthly ban-exclusion mechanism in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the exclusion table created by migration
`migrations/0071_monthly_ban_exclusions.sql`; the ban test it relies on
(`backend/projects/account-bans.ts`, the participation-ban query, fed
by the maintainer-ban table of migration 0066 and the account-release
table of migration 0072); the monthly obligation writer that applies
it (`backend/payments/monthly.ts`, the obligation-creation function,
the award-state fold, and the commitment guard); the recipient award
listing that hides excluded awards (`backend/payments/handler.ts`);
the monthly attestation that audits the exclusions
(`backend/payments/monthly-attestation.ts`); the payment documentation
(`backend/payments/README.md`, the obligations section); and the
product rule in `docs/slop-product-requirements.md` (PRD sections 6
and 7, monthly allocations and the automatic monthly process).

## Claim

A monthly award whose recipient has an active project-maintainer ban
is excluded when the month's obligations are funded, not when the
month is frozen: the exclusion is recorded in its own permanent table
with the exact ban decision as evidence, the recipient gets no
obligation and no vault funds are reserved for the award, and a later
release of the account does not revive that month's award — while an
award already reserved on chain before the ban keeps its funding.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The exclusion table pins the ban decision to the frozen month

Migration 0071 creates `monthly_payment_exclusions` with one row per
excluded award: project, period, and GitHub user id as the key; the
network, vault, and source digest of the award; the enforcement id of
the ban; and the creation time. Two foreign keys bind the row to the
evidence: the frozen monthly run it belongs to, and the exact
maintainer-ban row (enforcement id plus GitHub id) that caused it.
A second row cannot claim the same award in the same vault — the
network, vault, and source digest are unique together — and the row
itself is final: an update is refused as immutable and a delete as
permanent.

### 2. "Active ban" means a ban with no release

The ban test is a single shared query in `backend/projects/account-bans.ts`.
It looks for a maintainer-ban row for the GitHub id, joined to its
enforcement record, where no release row exists in
`project_account_reinstatements` for that enforcement and that
account. The same query gates the rest of the platform — security
report intake, trace persistence, the monthly freeze, and the monthly
settings write — so the exclusion uses the same definition of "banned"
as everything else. A ban therefore stops counting the moment a
release is recorded, and not before.

### 3. The ban is evaluated at funding time, in one atomic batch

Freezing a month checks only the actor who finalizes it; recipients
are not checked then. The check happens in the obligation-creation
function, which first captures one decision per frozen award — the
recipient, the award's source digest, and the enforcement id the ban
query returns for that recipient, or nothing when there is no ban.
It then writes in a single batch: stamp the run with the creation
time, insert an exclusion row for each decided award, and insert an
obligation for every snapshot award that is not excluded. The run
stamp itself re-checks the captured decisions against the live bans:
if any award's live ban decision differs from the captured one, the
stamp writes zero rows and the coordinator retries instead of funding
a stale decision. A ban that lands mid-write therefore delays the
month rather than slipping past it.

An award is excluded only when its recipient has a live ban decision
and the award is not already held on chain. An award already reserved
under its source digest is left out of the excluded set, and the
funding-need calculation likewise skips excluded awards, so a banned
recipient's award reserves no vault funds and does not delay the
other recipients. The exclusion insert also skips any recipient who
already holds a monthly obligation for that month, and re-running the
insert is a no-op. The documentation states the same rule in plain
words: before creating new obligations the coordinator excludes
accounts with an active moderator ban, records the exact ban, keeps
the original frozen snapshot, and excluded amounts neither delay other
recipients nor become their extra awards; previously funded
obligations remain valid.

### 4. What the excluded recipient sees

The owner view of a frozen month marks an excluded award with the
state `excluded` and zero gross, fee, and net amounts. A direct
commitment attempt for such an award fails with 403 and the code
`award_excluded`, with the message that the account was banned before
the award was funded. The contributor's own monthly-award listing
omits excluded source digests entirely. The monthly attestation
requires the same accounting from the other side: every snapshot
award omitted from the funded set must have an immutable
funding-time exclusion record, so a later ban cannot revoke a funded
right and an unexplained omission fails attestation. No notification
call references the exclusion table, so the exclusion surfaces only
in the owner view and the attestation, not as an inbox event.

### 5. A later release does not revive the excluded month

Obligations are created exactly once per frozen month: once the run
carries a creation time, a later pass reports "already-created" and
writes nothing. Because the exclusion row is permanent and the
obligation write for that month has already happened, releasing the
account afterwards clears the ban query for later months but creates
no obligation for the month that already excluded it. The frozen
snapshot itself is never rewritten — the award stays in it, and the
exclusion row is the record of why it was not funded.

## Verification

Replayed the schema locally in a scratch SQLite database: migrations
0001–0072 applied verbatim, in order (128 files, no failures), with
the 0072 rebuild preserving every enforcement row. On a frozen month
with two awards, running the obligation writer's three statements
verbatim — the run stamp with the captured ban decisions, the
exclusion insert, and the obligation insert — produced exactly one
exclusion row for the banned recipient, carrying the ban's enforcement
id and the award's source digest, and exactly one obligation, for the
unbanned recipient. Re-running the exclusion insert added nothing.
An update and a delete of the exclusion row were both refused; an
exclusion naming an unknown enforcement or an unknown run was refused
by the foreign keys; and a second exclusion claiming the same source
digest in the same vault was refused by the uniqueness rule. An
exclusion insert over a recipient who already held an obligation for
that month wrote zero rows, and a run stamp fed stale ban decisions
wrote zero rows, so the coordinator would retry. After recording an
account release by a different moderator, the ban query went silent
for the released account — while the month's exclusion row and its
single obligation were unchanged. The payment test suite pins the
same behavior: a banned recipient excluded while the other is funded,
a ban racing the funding write forcing a retry, a later ban preserving
already-funded awards, and the owner view showing the excluded award
with zero amounts while its commitment attempt fails as excluded.

## Notes

The packet covers the monthly EVM/Solana-shared obligation writer;
the chain-specific reservation that follows an obligation (EVM
reserve versus Solana admission) is a separate mechanism. The
exclusion applies per frozen month: a ban that starts after a month's
obligations are created leaves that month alone, and a release before
a month's obligations are created means that month never excludes the
account. Whether an excluded recipient is told through any channel
other than the owner view and attestation was not found in the
sources checked — no notification path references the exclusion
table.

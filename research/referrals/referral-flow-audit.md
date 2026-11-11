# Referrals — invite, attribution, accrual amounts, and the tier question, audited (Issue #4)

## Target

The referral program of the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438`, end to end: how a referrer
is named and recorded (`src/ProjectProposalPage.tsx`,
`backend/projects/handler.ts`, `migrations/0055_project_referrer.sql`),
what the recorded referrer earns and under which limits
(`workers/referral-accrual/`), whether any tier structure exists, what
the claim step connects to (`backend/referrals/`, PRD section 11), and
what of this is public versus server-only. Packet checker:
`scripts/verify-referrals.py`; tests: `tests/test_verify_referrals.py`.

Scope boundary with neighbouring packets: the step-by-step claim flow
is PR #31's packet (Issue #19), the accrual cutoff and period
selection are PR #45's and PR #50's, and the accrual worker's place
among the 13 workers is PR #44's. This packet covers what those do
not: the attribution rules at capture, the accrual amounts and caps
as one audited chain, the tier question, and the public/server split.

## Claim

SLOPCASH referrals are project referrals with one flat rate and no
tiers: a referrer named once — and thereafter immutably — on a project
application earns 3 program tokens per USDC of that project's
finalized stablecoin payouts inside a 12-month window, bounded by a
250,000-token per-project cap and a 2,000,000-token lifetime pool; the
program is fully implemented but inactive, and no accrual file has
ever been filed.

## Evidence

### The invite is a named login on a project application — there is no contributor invite system

- The only invite surface is a link to the project proposal page
  carrying a login: `src/ProjectProposalPage.tsx` reads
  `?ref=<login>` from the URL (`initialReferrer`, lines 377–390) and
  keeps it in browser storage under its own key
  (`slop:project-referrer:v1`, lines 104–108) so a resumed draft keeps
  the attribution. The worker README states the same in one line: a
  maintainer submitting at `/projects/new` may name the referrer via
  `?ref=<login>` (`workers/referral-accrual/README.md`, "What a
  referral is").
- A whole-tree search for a person-to-person invite or referred-by
  record (`referred_by`, `referredBy`, `invited_by`) returns no hits,
  and "invite" appears nowhere in the referral code or docs. The
  program is explicitly "not a contributor referral program"
  (`workers/referral-accrual/README.md`, lines 13–14): it rewards whoever
  brought a *project* to the platform.
- Capture is validated on the server at submission
  (`backend/projects/handler.ts`, `resolveReferrer`, lines 949–1000):
  the login must resolve to a GitHub actor who has signed in to
  slop.cash; self-referral, the project steward, and team accounts
  (administrators, moderators) are refused with HTTP 422.
- The record is written once on the application, copied to the
  project on approval, and locked: `migrations/0055_project_referrer.sql`
  requires the id/login pair together and raises `application
  referrer is immutable` on any later change (lines 19–31); the same
  immutability is specified in PRD section 11 (line 730).

### Accrual: only finalized payouts of referred projects, one flat rate

- Candidates are finalized payouts, nothing else
  (`workers/referral-accrual/store.ts`, `candidates()`, line 118):
  `payment_obligations` rows in state `paid` whose `paid` event falls
  in the period, on projects with `referrer_github_id IS NOT NULL`,
  excluding obligations an earlier run already judged. Listings,
  pledges, deposits and points accrue nothing (worker README).
- Each candidate is judged in observation order into exactly one of
  seven outcomes (`workers/referral-accrual/core.ts`, `Outcome`,
  line 27): `asset_not_eligible` (payout asset is not a reference
  stablecoin of its network with six decimals — a project-token
  payout has no fixed dollar value and accrues nothing),
  `referrer_excluded` (team account from operator configuration, or
  a participation-banned referrer), `held` (project under an active
  hold), `window_closed`, `project_cap`, `pool_cap`, or `accrued`.
- The amount is a single multiplication: `grossBase ×
  rateBasePerMicro` (`core.ts`, line 365), then bounded by the
  remaining per-project cap and the remaining pool
  (`cappedReferralAccrual`, imported from
  `workers/verified-policy.ts`, line 54). The published numbers are
  PRD section 11, line 732: initial rate **3 program tokens per
  1 USDC of gross payout**, calculated per stablecoin micro-unit;
  **12-month** window from the project's first paid obligation
  (window arithmetic in `core.ts`, `windowEnd`, line 182);
  **250,000-token** lifetime cap per referred project;
  **2,000,000-token** lifetime pool; first period **November 2026**;
  rate changes are prospective and filed accruals never change.
- The code holds no rate constant: rate, window, pool and caps are
  operator environment values (`workers/referral-accrual/config.ts`:
  `REFERRAL_RATE_BASE_PER_MICRO`, `REFERRAL_WINDOW_MONTHS`,
  `REFERRAL_POOL_BASE`, `REFERRAL_PROJECT_CAP_BASE`, lines 183–204),
  so the PRD figures above are the published initial configuration,
  not values a reader can recompute from constants in the code.

### Tiers: none exist

- The word "tier" appears in none of the referral code paths — the
  claims backend, the accrual worker, the claims UI and library, and
  the `ReferralDistributor` contract (the checker in this PR scans
  all nine files; 0 hits). Every referrer earns at the same flat
  rate; what differentiates outcomes is eligibility (stablecoin,
  window, holds, bans) and the two caps, not a referrer tier. The
  "tiers" in Issue #4's title have no counterpart in the code or the
  PRD at this commit.

### The claim step, at the boundary this packet owns

- Filed accruals become cumulative Merkle roots on Robinhood Chain;
  a referrer claims the cumulative total for the wallet pinned to
  the root, the owner may void only the latest root before its first
  successful claim, and a successful claim seals the root (PRD
  section 11, line 738). Earnings separates accrued, pending,
  claimable and claimed amounts from cached finalized chain evidence.
  The step-by-step browser/API claim flow itself is PR #31's packet;
  this packet adds only that a claim can only ever pay what the
  accrual chain above filed — and nothing has been filed (below).

### Public versus server-only, and activation state

- Public: the filed accrual files themselves are a public read
  route, `GET /api/v1/referrals/accruals`
  (`backend/referrals/handler.ts`, line 23; header comment lines
  1–8: no session or key is read, there is no write route) — the
  files are the exact bytes the job filed so anyone can recompute an
  epoch from the public payment record.
- Checked live on 2026-11-11: that index answers
  `{"schema":"slop-referral-accrual-index-v1","files":[]}` — zero
  files. The program is gated off in code
  (`workers/referral-accrual/config.ts`, line 126:
  `REFERRAL_PROGRAM_ENABLED` must be exactly `"true"`; accrual modes
  are `off` / `dry_run` / `live`), and PRD section 11 (lines 724–742)
  records why: reactivation was proposed 2026-11-09 and agreed
  2026-11-10, but accrual stays `off` or `dry_run` until funding is
  agreed — funding means a decision-market proposal transferring
  2,000,000 tokens from the treasury to the mainnet distributor —
  and the owner explicitly activates posting.
- Server-only: the attribution itself. The public project record
  carries no referrer field (checked live: the string `referrer`
  does not occur in `GET /api/v1/projects/asi`); the referrer is
  visible in the applicant/steward application and project views
  (`backend/projects/handler.ts`, lines 904–917), i.e. behind a
  session. Individual accrual judging inputs (payment obligations,
  holds, bans) likewise live in the server database; only their
  filed outcomes are published.

## Verification

- `python3 scripts/verify-referrals.py <slopdotcash checkout>` —
  parses the five published numbers out of PRD section 11 and
  matches them to the values quoted above; scans the nine referral
  code paths for "tier" (0 hits); checks the four submission
  refusals, the 0055 pair and immutability triggers, the exact
  seven-outcome set, the candidate SQL predicates, and the program
  flag/mode gates; then reads the two live endpoints (accrual index
  schema with 0 files; no `referrer` in the public project record).
  Observed on 2026-11-11 against commit `ced75d782`: **ALL CHECKS
  PASSED** (22 checks). `--offline` skips the two live reads.
- `python3 -m pytest tests/` — 4 new tests over the checker's
  parsing helpers pass; the existing `tests/test_verify_selector.py`
  still passes (4/4). Run here by direct function execution because
  pytest is not installed in this environment; outputs recorded with
  the packet workpapers.
- Traced by hand: `ProjectProposalPage.tsx` `initialReferrer` →
  `backend/projects/handler.ts` `resolveReferrer` → migration 0055
  triggers → `store.ts` `candidates()` → `core.ts` judging order and
  line-365 computation → `cappedReferralAccrual` bounds.

## Notes

- Issue #4's "Where to look" names
  `docs/referral-distributor-testnet-runbook.md`; no file by that
  name exists anywhere in the tree at this commit (checked with
  `git ls-tree`). The operator documentation that does exist is
  `workers/referral-accrual/README.md`, which this packet cites
  instead.
- The accrual worker's internal mechanics beyond amounts and caps —
  period selection, the accrual cutoff, root posting — are covered
  by PR #50, PR #45 and PR #44 and are not repeated here.
- All amounts are program tokens (the SLOP token at
  `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain,
  PRD section 11 line 742); nothing in this packet is a claim that
  any amount is payable today — the funding transfer has not
  happened in any public record this packet could read, and the
  live accrual index is empty.

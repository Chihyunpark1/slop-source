# Security — the bounty program, the private report flow, and case access control

## Target

Issue #5 — the security features of the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438`: the program terms schema
(`src/lib/security-bounty.mjs`), the public offer and editor
(`src/SecurityBounty.tsx`, `src/SecurityOffer.tsx`,
`src/SecurityProgramEditor.tsx`), the private report form and summary
(`src/PrivateReportForm.tsx`, `src/PrivateReportSummary.tsx`), the case
backend (`backend/security/`, especially its README and
`project-access.ts`), the settlement worker
(`workers/security-payments/`), PRD sections 8–10, the repository's
`SECURITY.md`, and the live public registry
(`GET https://slop.cash/api/v1/projects`, swept 2026-11-11).
Packet: `research/security/security-program.md`; checker:
`scripts/verify-security-program.py`; tests:
`tests/test_verify_security_program.py`.

This packet documents the program as an institution — its published
terms, its report procedure, and its documented roles. It contains no
vulnerability, exploit, or bypass material, and it evaluates no access
control beyond what the public code documents.

## Claim

The security bounty is a published-terms, private-case system: the
terms are public data frozen into each report's receipt at submission
time, cases are never public, the standard award split is 75% to the
researcher and 25% to Slop with shares derived (never stored) from a
gross amount that must divide by four, and — read live on 2026-11-11 —
only 2 of the 32 registered projects publish a `securityBounty` program
in the registry, both of them open, after-approval pledges with no
funds shown as available.

## Evidence

### 1. Program terms: one schema, five statuses, two eligibility kinds

- Terms live in the project's registry manifest as the optional
  `securityBounty` section; every edit appends an immutable project
  revision, and a program cannot be removed — existing cases keep
  their receipt terms and funded obligations survive a pause or
  closure (`backend/security/README.md`, "Program terms";
  `src/lib/security-bounty.mjs` header comment: the terms live in the
  project's D1 manifest revision, case data never enters the
  structure). The published terms are served at
  `/projects/:id/terms.json` and `/projects/:id/security`.
- Statuses are exactly `draft`, `pending-approval`, `open`, `paused`,
  `closed` (`SECURITY_PROGRAM_STATUSES` in
  `src/lib/security-bounty.mjs`). Reward modes are `bounty-only`
  (requires a $0 monthly pool with payments disabled) and `separate`.
- New programs use `eligibility: "in-scope-security"` — the owner
  judges a report against the published scope and criteria. Existing
  programs keep `eligibility: "critical-loss-of-funds"` with its
  severity and impact restrictions. Eligibility is frozen at receipt,
  so later edits cannot change an existing report's conditions
  (backend README, "Program terms").
- A registered project accepts private reports even with no bounty
  terms and no funds; without terms, intake uses the primary
  registered repository and receipts freeze `terms: null` and
  `award_state: not-applicable`, so later terms never retroactively
  grant an award to an earlier report (backend README, introduction).
  PRD section 8 says the same: any registered user may report,
  including to a project without a bounty, and an unpaid intake
  promises no award.

### 2. The split and the amount

- `SECURITY_SPLIT` is 7,500 / 2,500 basis points — 75% researcher,
  25% Slop — described in the schema as "the owner-approved split"
  (`src/lib/security-bounty.mjs`). `SECURITY_FULL_AWARD_SPLIT` is
  10,000 / 0, "an admin-approved exception that pays the whole award
  to the researcher"; PRD section 8 adds that only
  administrator-controlled manifest terms may grant a split exception.
- `amount.grossMinor` is the published gross award per finding, an
  integer in minor units that must be divisible by four under the
  standard split so both shares are exact; shares are derived at read
  time, never stored (backend README, "Program terms"). PRD section 8:
  no ordinary 2% fee or claim fee is added, and exact gross and net
  amounts are shown before authorization.
- The public offer component renders exactly this arithmetic: the
  researcher amount prominently, then the gross total and the Slop
  share, or — under a full-award split — a statement that Slop takes
  no share and no payout fee (`src/SecurityOffer.tsx`).
- Funding rules: `status: "open"` normally requires
  `funding.state: "verified-available"` with an evidence reference;
  `fundingPolicy: "after-approval"` explicitly permits pledged terms
  with no claim that money is available. `capacity.awards: null`
  means each first qualifying finding is considered separately, not a
  fixed award count. A program without a reviewed bounty vault
  reserves nothing (backend README, "Program terms", incl. owner
  decision D10).

### 3. The live registry, swept in full (2026-11-11)

`python3 scripts/verify-security-program.py` (live mode) output:

```text
mode: live (https://slop.cash/api/v1/projects)
projects swept: 32
security bounty programs: 2
  status open: 2
- orbio-contracts: status=open eligibility=in-scope-security fundingPolicy=after-approval funding=pledged rewardMode=bounty-only gross=2000000000 CREDIT (decimals 6) split=7500/2500
    derived shares: researcher 1500000000, slop 500000000 (minor units)
- umia-protocol: status=open eligibility=critical-loss-of-funds fundingPolicy=after-approval funding=pledged rewardMode=separate gross=10000000000 USDC (decimals 6) split=7500/2500
    derived shares: researcher 7500000000, slop 500000000 (minor units)
all program checks passed
```

- Umia Protocol: 10,000 USDC gross per accepted distinct critical
  loss-of-funds finding → 7,500 researcher / 2,500 Slop; response
  targets in its published terms are acknowledge 24 hours, triage
  3 business days, updates every 7 days (per-project record,
  `GET /api/v1/projects/umia-protocol`). This matches the protected
  terms in PRD section 8 exactly.
- Orbio Contracts: 2,000 CREDIT gross (2,000,000,000 minor at
  6 decimals) under the newer `in-scope-security` eligibility →
  1,500 / 500 derived shares.
- Both programs are pledges: `fundingPolicy: "after-approval"`,
  `funding.state: "pledged"`, no verified-available funding shown.
- The third program described in the documents — the Slop mainnet
  contracts program, $10,000 per accepted critical loss-of-funds
  finding paid entirely to the first qualifying reporter (PRD
  section 8 "Protected program terms"; `SECURITY.md` in the codebase
  root) — does **not** appear as a `securityBounty` block in the
  `slopdotcash` project's registry record, and its published terms
  document reads `"securityBounty": null`
  (`GET https://slop.cash/projects/slopdotcash/terms.json`,
  read 2026-11-11). `SECURITY.md` itself states the binding terms
  are the ones published on the project's security page and that
  until they are published there no award is promised; whether the
  security page serves terms from the D1 revision beyond these two
  public surfaces was not verifiable from the registry data alone,
  so this packet records the registry state only.

### 4. How an award is decided and paid

Documented flow (`backend/security/README.md`, "Awards" and payment
sections; PRD section 8, "Award, payment, and disclosure"):

1. A technical approver records the finding decision (`decide`:
   outcome, severity, loss, scope as guidance). A confirmed finding
   with paid terms then waits for the owner's award decision:
   `decision: "none"` makes the award ineligible (the reporter can
   appeal); `decision: "amount"` selects an exact gross — under
   after-approval terms it must be the frozen published amount.
2. A direct award can be approved without a vault and reserves no
   wallet funds. A vault-backed award stays pending until verified
   funds cover it; the reservation insert itself checks the bounty
   vault's unreserved finalized free balance and writes nothing if it
   does not cover. One root cause reserves once per project; a
   reserved or approved award is never redecided or withdrawn.
3. Payment uses one of two rails. Direct payment: a financial
   approver prepares an unsigned plan from their verified wallet and
   the payer signs and broadcasts it themselves — Slop never signs or
   broadcasts. Vault settlement: the existing escrow rails with the
   security policy attached at vault registration
   (`feeBasisPoints: 2500`, `withdrawalFeeBasisPoints: 200` in
   `attachBountyVault`), executed by `workers/security-payments/` —
   the same recovery engine and approved executors as ordinary
   payments, but a separate private ledger and private notifications,
   with no fetch route and no public payment database binding
   (`workers/security-payments/index.ts` header comment). No action
   can manually mark an award paid; the case becomes paid only after
   every required transfer is finalized and reconciled.
4. Bounty vault balances stay private and never enter ordinary
   contribution payment totals (backend README, "Program terms").
   Public payment queries, notifications and aggregates never use the
   security settlement tables (backend README, "Existing vault
   settlement").
5. Appeals: a reporter may appeal a duplicate, out-of-scope or
   rejected finding, or a confirmed finding without an award.
   Slopbot triages every appeal first (an advisory draft only — it
   never decides, changes the case, or moves funds), and a moderator
   decides escalated disputes (backend README, "Awards";
   `approvers.dispute` names the program's dispute contact).

PR #32 covers the payout rails and the public payment record; this
packet covers the program side — the award decision flow above is
described only where it differs from ordinary payments (private
ledger, no manual paid marking, no monthly-payment fallback; PRD
section 8: private awards never use the automatic monthly-payment
fallback).

### 5. The private report flow

The researcher journey is published as eight steps (PRD section 8,
"Researcher journey"): open the project's confidential-report entry
or bounty offer → review scope, safe-test rules, funding status and
amounts → sign in and write the affected component, source revision,
impact and safe reproduction evidence → review the exact report,
eligibility and privacy terms, then submit → receive a durable Slop
receipt in the Inbox → follow screening and human review, provide
requested information or appeal privately → if awarded, confirm the
payment destination and follow funding/payment progress → track
remediation and any separately approved disclosure.

Mechanics documented in the public code:

- One route holds "Write report" and "Review and submit"; drafts live
  in account-and-project-bound session storage and are cleared on
  sign-out or account change; there is no server autosave and no
  attachment service (PRD section 8, "Offers and report intake").
- The durable intake path (`POST /api/v1/security-submissions`,
  `origin: "slop"`) stores the exact report in private object storage
  before any optional forwarding; the source receipt, frozen policy,
  case, submission metadata and the reporter Inbox notice commit
  together after the stored report's digest is checked. Report bodies
  are never in the database, public pages, logs, analytics,
  notifications or generated artifacts (backend README, "Durable
  Slop-first intake").
- Screening runs before the project owner is notified: an automated
  plausibility screen (states `queued`, `running`, `legitimate`,
  `needs-information`, `spam`, `unavailable`) that judges plausibility
  and evidence only — explicitly not an award, rejection or
  disclosure decision. Held reports stay readable to their reporter
  and current case authorities and are not automatically rejected or
  awarded (backend README). PRD section 8 adds: screening is
  advisory, separate from severity, acceptance, award, payment and
  disclosure, and no submitted code is executed.
- Human routing: a current technical maintainer can record `forward`
  or `request-information` with a private reason; the reporter can
  add a new immutable report version and rescreen; the original
  receipt time, bytes and terms never change (backend README).
- Submission states are `draft`, `submitting`, `uncertain`,
  `submitted`, `receipt-verified`, `failed`, `abandoned` (backend
  README, "Legacy GitHub-first private intake"). GitHub forwarding is
  optional, requires the reporter's explicit authorization, and is
  verified separately from the Slop receipt; a failed forward never
  loses the report or blocks private review, and the flow never
  falls back to a public issue (PRD section 8).
- Disclosure is a separate decision: recording it requires the
  latest disclosure decision to approve the exact redacted content
  (bound by its SHA-256); remediation, payment or an expired
  deadline never authorizes disclosure, and reporter recognition
  consent stays separate (backend README, "Disclosure approval
  records"; PRD section 8).
- The repository's own `SECURITY.md` gives the platform-level entry
  points: sign in and submit a private report on the project's
  security page, or use GitHub private vulnerability reporting; it
  instructs reporters never to open a public issue or PR containing
  an unpatched vulnerability, to use a minimal example with synthetic
  data, and never to include credentials or another person's private
  data.
- Rate and retention rules documented publicly: public report
  creation, evidence revisions and rescreening share ten admissions
  per account in a rolling hour; case, report and audit history is
  permanent (backend README, "Durable Slop-first intake").

### 6. Access control around security features

Roles are computed on every request from the session and the current
project revision, so a revision change or a revoked session removes
access at once (`backend/security/README.md`, "Roles"). The
documented role table:

| Role | Documented access |
| --- | --- |
| Reporter | Their own cases only; never another report, root cause, or triager. A reporter never acts on their own case. Any registered user may report; project membership is not required. |
| Technical approver (security maintainer, project owner or maintainer authority) | Every case of the project; decides findings, awards, remediation and disclosure; prepares the unsigned payment. |
| Triager | Only assigned cases; request information and remediation. |
| Financial approver | Only cases with an approved (or older reserved) award, and only award and payment fields; prepares the unsigned payment. Financial roles alone receive no report body. |
| Moderator | Only cases with an appeal or a related-party award review; decides them. |
| Platform admins, sponsors, the public | Nothing. (Administrators do not automatically gain private-case access — PRD section 9.) |

How the roles are established, as documented:

- Repository authority: the technical case-access grant for a
  registered project is checked against the project's stored
  repository before any private funds are read. Slop checks the
  actor's current GitHub repository permission through Slopbot's
  repository-access read; the grant requires the app installation to
  be present, the manifest to match the repository Slopbot returns,
  and the actor to be the manifest steward or hold `admin`
  permission on the repository (`backend/security/project-access.ts`,
  `repositoryReportingAuthority`). A permission-provider outage is
  retryable — it is never treated as a denial or as an empty scope.
- Program management: owners edit terms and open, pause or close the
  program in project settings through the project revision route,
  which checks current GitHub authority through Slopbot. The project
  steward or a repository admin manages contacts and the sponsor;
  ordinary write access cannot grant or remove private-case roles.
  The server sets funding evidence; an owner cannot supply it
  (backend README, "Program terms"). The editor component states the
  same split: it holds identity only, and "the API separately checks
  current repository authority" (`src/SecurityProgramEditor.tsx`).
- Moderators: the moderator role comes from a server-side Pages
  variable, `PROJECT_MODERATOR_GITHUB_IDS` (`backend/pages.ts`);
  PRD section 9 names the two moderator accounts. Escalated disputes
  go to a moderator; the technical decider cannot decide the appeal
  or the related-party review of their own case (backend README,
  "Roles").
- Request shaping: a caller without a role receives the same 404 as
  for a missing case; case reads are logged; responses are `private,
  no-store` and `noindex`; errors never log case data (backend
  README, "Routes"). Notification email about a case goes only to
  current case roles with operator-verified destinations and never
  contains a case identifier, amount, project or advisory (backend
  README, "Hosted services").
- Account bans interact with awards: a moderator account ban
  prevents proposing or approving a new bounty award or receiving a
  new reservation, checked again at write time for both the decision
  maker and the researcher; existing reservations are unchanged and
  the researcher can still read the case and appeal (backend README,
  closing section).

PR #49 maps the general operator gates (vetting, moderation,
cycles); this section covers only the security-case roles and the
repository-authority check that grants them.

### 7. What is public and what is server-only

| Public | Server-only / private |
| --- | --- |
| Program terms: scope, amounts, split, funding state, response targets, approvers, dispute and disclosure text (`/projects/:id/terms.json`, the security page) | Report bodies (private object storage; database holds references and digests only) |
| The registry record, including the `securityBounty` block (`GET /api/v1/projects`) | Case records, decisions, and the access audit log; reads are audited |
| Intake readiness observation (`GET /api/v1/security-programs/:id/intake`: `ready`/`disabled`/`unavailable`, `checkedAt`, `stale`) | Screening and analysis results (restricted event detail; only maintainers and assigned triagers see the analysis proposal) |
| This codebase and its PRD, including the role rules above | Bounty vault balances and the security settlement tables; never in public payment queries or aggregates |
| The number and terms of published programs (sweep above) | Award reservations and payment generations; on-chain settlement records expose actor numbers, addresses, times and amounts, but a random source commitment — never report data |

## Verification

- Re-read every cited source at the pinned commit `ced75d782` with
  `git show` from the public codebase: `src/lib/security-bounty.mjs`,
  `src/SecurityOffer.tsx`, `src/SecurityProgramEditor.tsx`,
  `backend/security/README.md`, `backend/security/project-access.ts`,
  `workers/security-payments/index.ts`, `SECURITY.md`, and PRD
  sections 8–10.
- Ran `python3 scripts/verify-security-program.py` live on
  2026-11-11: 32 projects swept, 2 programs found, both open
  after-approval pledges, every split summing to 10,000 bp and every
  standard-split gross divisible by four, derived shares exact —
  output quoted verbatim in Evidence §3. Ran the same checker with
  `--offline` against its embedded sample (3 records, 2 programs).
- Read `GET /api/v1/projects/umia-protocol` and
  `GET /api/v1/projects/slopdotcash` individually to confirm the
  sweep, and `GET https://slop.cash/projects/slopdotcash/terms.json`
  for the `"securityBounty": null` observation.
- Ran this repo's tests: 3 new tests in
  `tests/test_verify_security_program.py` pass, and the existing
  `tests/test_verify_selector.py` still passes (4/4). (pytest was not
  installed in this environment, so the test functions were executed
  directly; the repo CI installs pytest.)
- Relation to other packets: payout rails and the public payment
  record are PR #32 (Issue #3); general operator gates are PR #49
  (Issue #6); points disputes are PR #23 (Issue #2). No open PR
  covers the security program, the report flow, or security-case
  access control.
- Limits: the registry figures are a point-in-time read from
  2026-11-11 and can change with any project revision. The security
  page itself (`/projects/:id/security`) is a rendered app page and
  was not scraped; the packet relies on the two machine-readable
  public surfaces (registry record and terms.json) plus the
  published documents. No case, submission, or session-gated route
  was accessed; all live reads were public and read-only.

## Notes

- This packet intentionally stays at the level of the published
  program: terms, procedure, and documented roles. It reports no
  vulnerability and assesses no weakness; the codebase's own rule —
  report security findings only privately — is quoted in Evidence §5
  as part of the documented flow.
- Where the documents and the live registry differ (the mainnet
  contracts program, Evidence §3), the packet records both and
  asserts only what the registry read shows.

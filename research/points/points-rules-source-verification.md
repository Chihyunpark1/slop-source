# Points rules — primary-source verification (balances, decay, disputes, claims)

## Target

Issue #2: the points system of the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), at development commit
`ced75d782d5836f60d84f46d50604f75a5852438` (tip measured 2026-11-11):
`docs/slop-product-requirements.md` section 7, `src/lib/points.ts`,
`src/lib/scoring-policy.ts`, `src/lib/score-records.ts`,
`src/lib/value-assessment.ts`, `src/lib/leaderboard.ts`,
`backend/points/disputes.ts`, `workers/slopbot/penalties.ts`,
`workers/verified-policy.ts`, `workers/slopbot/appeals.ts`,
`migrations/0044_points_immutable_history.sql`, and the live public
record at `https://slop.cash/data/points-summary.json`.

This packet is the source audit behind the rules, not a summary: every
published number below is pinned to the code constant that produces
it, and the arithmetic is cross-checked across the independent
locations that state it. (Issue #17 asks for a plain summary of the
points rules; this packet covers #2's full scope — original sources,
numeric verification, decay, immutability, disputes, and what is
public versus server-only.)

## Claim

The points rules published in PRD section 7 are exactly the rules the
public code implements — contribution tiers, review bands, penalty
debits, and the ×10 thirds-to-points conversion agree across the PRD,
the scoring constants, and the penalty function — and balances change
only through appended journal revisions (awards, corrections, and
month-bounded penalty debits): there is no decay mechanism, points
are not themselves claimable or redeemable, and disputes are private
appeals against immutable revisions.

## Evidence

All line numbers are for commit `ced75d782` above. "Confirmed" means
read in the source and, where a number is involved, recomputed;
"not found" means searched for in the stated scope and absent.

### 1. How points are earned (confirmed)

Points are computed in integer "thirds" and converted at a fixed
rate: `POINTS_PER_THIRD = 10` (`src/lib/points.ts:371`, under the rule
version `POINTS_RULE = "slop-points-v1"`, `src/lib/points.ts:25`).

| Source | Values (thirds) | Converted (points) |
| --- | --- | --- |
| Contribution tiers, `src/lib/score-records.ts:9-16` | micro 1, small 3, medium 9, large 24, xl 45, exceptional 75 | 10, 30, 90, 240, 450, 750 |
| Review bands, `src/lib/value-assessment.ts:9-15` | triage 1, standard 3, deep 9, specialist 24 | 10, 30, 90, 240 |
| PRD size table, `docs/slop-product-requirements.md:372-379` | — | 10, 30, 90, 240, 450, 750 |
| PRD review table, `docs/slop-product-requirements.md:381-386` | — | 10, 30, 90, 240 |

The converted columns are identical to the PRD tables (recomputed in
Verification below). The same tiers render on the public rules page
from the same constant (`src/PointsRules.tsx:18-42`).

Further earning rules, each cited:

- Every accepted merge receives at least 10 points, including a
  zero-size assessment; split or related PRs are grouped into one
  work unit; duplicate credit across commits, stacked PRs, and
  indirect merges is prevented; no account-level caps
  (`docs/slop-product-requirements.md:388`).
- Reviews are credited separately from merge credit. Bots,
  self-review, post-merge reviews, repeated comments, and duplicate
  or empty reviews are excluded; a useful review may validate without
  requesting changes (`docs/slop-product-requirements.md:390`).
- Review credit: at most the first five distinct qualifying reviewers
  (`MAX_CREDITED_REVIEWERS = 5`, `src/lib/scoring-policy.ts:20`;
  PRD line 392). The pool is the sum of the credited reviewers'
  highest bands, capped at the PR's assessed size, with a 10-point
  minimum, split proportionally by largest remainder in 10-point
  increments; ties break by first qualifying review time, then review
  node ID (`docs/slop-product-requirements.md:392`;
  `src/lib/scoring-policy.ts:92-104` and the published plain-language
  summary the code generates at `src/lib/leaderboard.ts:1478`).
- One more award category exists on the points side of payouts: a
  paid monthly-pool cycle adds a fixed 25-point `payout-received`
  award per recipient, project, and cycle, independent of the amount
  (`src/lib/payout-points.ts:6-7`). How money itself moves is issue
  #3's scope, and cycle pages are issue #9's.
- Policy boundary: work accepted before 2026-11-01 keeps the earlier
  Slop Score v2 / SCR-05 rules; the value policy
  (`slop-value-v1`, rubric `slop-value-2026-10-09`) applies from
  2026-11-01, with eligible unpaid September–October 2026 work scored
  under the current bands (`src/lib/scoring-policy.ts:1-10,36-43`;
  `src/lib/value-assessment.ts:8`). Welcome and X-connection awards
  stopped on 24 October 2026; earlier ones are preserved
  (`docs/slop-product-requirements.md:396`).

### 2. What changes a balance (confirmed)

Balances are the sum of an append-only journal of revisions
(`src/lib/points.ts`: `PointRevision` carries `previous`,
`sourceDigest`, and `sourceRule`; the current state is the latest
revision per award key, `latestPoints` at line 419). A balance moves
only when a new revision is appended:

- a new award (categories seen in the code: `merged-pull-request` and
  `evidence` score events, plus the journal-only categories
  `payout-received` and `slopbot-penalty`,
  `src/lib/points.ts:32`);
- a correction, appended as a decision with a delta on a new revision
  — earlier records are never rewritten
  (`docs/slop-product-requirements.md:402`, "Append corrections;
  never rewrite earlier records");
- a Slopbot penalty debit (next section).

### 3. Decay (not found — no decay mechanism)

A case-insensitive search for `decay` across `src/`, `backend/`,
`workers/`, `docs/`, `scripts/`, and `migrations/` of the target
commit returns no hits. The PRD states the opposite of decay: "Do
not apply account-level caps or diminishing credit"
(`docs/slop-product-requirements.md:388`). The only reductions that
exist are penalty debits and appended corrections:

| Penalty (confirmed) | Debit (thirds) | Debit (points) |
| --- | --- | --- |
| spam | 3 | 30 |
| scam or malicious | 24 | 240 |
| clear violation of a quoted project rule (busywork/gaming) | 1 | 10 |
| low quality, duplicate, out of scope | 0 | 0 |

Debits are defined once in `penaltyDebit`
(`workers/verified-policy.ts:21-31`), tabulated in
`workers/slopbot/penalties.ts:32-58` (table version
`slopbot-penalties-v1`), and match the PRD penalty table in section
7. A debit affects only that UTC month's accepted-work points for
the project, cannot reduce them below zero, cannot change an
approved, scheduled, or paid award, and is recorded once — an upheld
appeal or a maintainer reopen removes it
(`docs/slop-product-requirements.md:423`;
`src/lib/leaderboard.ts:1478`).

### 4. History and immutability guarantees (confirmed)

- The database enforces immutability directly:
  `migrations/0044_points_immutable_history.sql` installs triggers
  that abort replacing an existing revision, creating a second root
  revision for a key, or branching a successor chain, and that make
  completed points batches un-updatable and un-deletable.
- Revision integrity is verified on read: a dispute lookup recomputes
  the revision ID from its payload and fails if it does not match
  (`backend/points/disputes.ts:33-48`).
- The journal is published: an index at `/data/points.json` with
  shards under `/data/points/`, assembled by
  `scripts/generate-points.ts` (lines 47, 69-77, 106). A retained
  historical snapshot is also committed in the repo at
  `data/points/history.json` (rule `slop-points-v1`, generated
  2026-09-21, 16,278 revisions, coverage of four repositories —
  counted by parsing the file, see Verification).

### 5. Dispute flow (confirmed)

- A dispute is "a private dispute of a retained, immutable Points
  revision" (`backend/points/disputes.ts:1`). Only the award
  recipient can open one, against a specific revision, with a
  statement; opening sets a due date 7 days out
  (`APPEAL_RESOLUTION_DAYS = 7`, `workers/slopbot/appeals.ts:13`).
- States are `triage` → `review` (escalated) → `resolved`
  (`backend/points/disputes.ts:50-65`). Visibility is restricted: the
  appellant can always read their dispute; a moderator can read it
  only after escalation (`backend/points/disputes.ts:182-184`).
- Only a moderator may decide, only after escalation, and only with
  action `uphold` or `deny` (`backend/points/disputes.ts:203,
  214-225`). An upheld dispute reverses the debit it targets (PRD
  line 423; section 3 above).

### 6. Claims — what points can and cannot be claimed as (confirmed)

- Points themselves are not claimable: the platform's own notice,
  published with the points code, is "Points have no cash value and
  cannot be transferred or redeemed." (`src/lib/points.ts:26-27`).
  The scoring policy states the same separation: "a score is never
  an award" (`src/lib/scoring-policy.ts:9`).
- What points do determine is reward shares: "Only accepted-work
  Points for the project and period determine reward shares", and
  monthly and lifetime totals are views of the same history
  (`docs/slop-product-requirements.md:368-370`).
- No token allocation list is published in the current codebase:
  `public/contributor-allocation.json` at the target commit contains
  exactly `{ "distribution": null }` (read directly). Any claim or
  registration flow for a token distribution is therefore not
  verifiable from public material at this commit — marked unknown,
  not guessed.

### 7. Public data versus server-only (confirmed where stated)

Public:

- `/data/points-summary.json` — the all-time per-contributor totals
  the home page reads (`src/lib/points-summary.ts:1-5`). Live check
  on 2026-11-11: `ruleVersion` `slop-points-v1`, `generatedAt`
  `2026-11-10T11:02:50.351Z`, totals of 989 contributors and 750,570
  points, index digest beginning `414e21ca`. The file's own schema
  requires the contributor count to equal the array length, entries
  sorted descending, and entry totals summing to the headline total
  (`src/lib/points-summary.ts:21-56`); every total visible in the
  fetched file is a multiple of 10, consistent with the 10-point
  allocation increments in the PRD.
- The full journal index and shards (section 4), project
  leaderboards, profiles, and cycle pages.

Server-only:

- Dispute statements and case data are private by construction
  (section 5), and the PRD forbids publishing private case amounts,
  counts, or queues through profiles, balances, rankings, or cycles
  (`docs/slop-product-requirements.md`, section 7, "Discovery and
  public records").
- Anything beyond the published journal — for example the internal
  assessment manifests behind individual value assessments — could
  not be verified from public material in this pass and is left
  unknown rather than described.

## Verification

All checks were run 2026-11-11 against a fresh clone of
`SlopDotCash/slopdotcash` at `ced75d782`.

1. Arithmetic cross-check (scripted, parsing the constants out of the
   source files rather than retyping them): tiers from
   `score-records.ts` × `POINTS_PER_THIRD` from `points.ts` reproduce
   the PRD size table exactly (6 of 6 values); review bands from
   `value-assessment.ts` reproduce the PRD review table exactly (4 of
   4); `penaltyDebit` return values × 10 reproduce the PRD penalty
   debits (spam 30, scam 240, quoted-rule 10, others 0).
2. Decay search: `grep -rni decay src backend workers docs scripts
   migrations` on the target commit — no hits outside test files,
   and no hits at all in the listed source directories.
3. Live public record: fetched `https://slop.cash/data/points-summary.json`
   and read the header values quoted in section 7 (rule version,
   generation time, contributor and point totals, digest prefix);
   confirmed every total visible in the response is a multiple of 10.
4. Committed history snapshot: parsed `data/points/history.json` —
   16,278 revisions, all of category `merged-pull-request`, rule
   `slop-points-v1`, generated 2026-09-21T18:20:07.791Z, coverage of
   four repositories (elizaOS/eliza, elizaOS/asi,
   heirlabs/element-sdk, elizaOS/proximityprize).
5. Allocation file: read `public/contributor-allocation.json` at the
   target commit — content is `{ "distribution": null }`.
6. Every other statement cites its file and line above; a reviewer
   can re-read each location in minutes.

## Notes

- Scope boundary: this packet documents the points rules and their
  source grounding. Payment execution (issue #3), referral claims
  (issue #4), and cycle/standings pages (issue #9) are separate
  issues; they are referenced only where the points rules themselves
  touch them (reward shares, the payout-received award).
- The pre-November legacy rules (Slop Score v2 / SCR-05) are
  documented in the target code only as a preserved boundary
  (`src/lib/scoring-policy.ts:1-10`); reconstructing the full legacy
  rule set is a separate packet if the maintainer wants it.
- No source code is reproduced in this packet; behavior is summarized
  and cited by file path and line.

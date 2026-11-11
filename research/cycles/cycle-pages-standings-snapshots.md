# Cycles & standings — the pages, the standings, and the snapshots behind them

## Target

Issue #9: the cycle and standings surface of the public SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438` — `src/CyclePages.tsx`,
`src/HomeStandings.tsx`, `src/AutomaticMonthlyPayment.tsx`, the
`cycles/` directory, and the three published artifacts those pages
read: `/data/points-summary.json`, `/data/leaderboard.json` (a
manifest over snapshot parts), and `/data/cycles/index.json`, all
fetched live from slop.cash on 2026-11-11.

The packet is `research/cycles/cycle-pages-standings-snapshots.md`;
the checker is `scripts/verify-cycle-standings.py`; its tests are
`tests/test_verify_cycle_standings.py`.

## Claim

Everything the cycle pages and standings display is rendered from
three published static snapshots whose numbers recompute exactly
from the documented rules — a cycle is a UTC calendar month, standings
order by score with shared competition ranks, and from 2026-11 the
owner-change window closes 72 hours after the month ends — while the
monthly allocations and changes behind those pages stay private in
D1, and the owner's automatic-payment switch is an on-chain vault
setting that the UI accepts only against finalized chain state.

## Evidence

### What a cycle is, and what the cycle pages show

- A cycle id is `YYYY-MM`, validated by `/^\d{4}-(0[1-9]|1[0-2])$/`
  (`src/CyclePages.tsx`, `CyclePage`), and its contribution window is
  the UTC calendar month `[first, next first)`:
  `cycleBounds` delegates to `periodBounds`
  (`src/lib/project-view.ts:220-226`), and every published cycle
  record carries that window as `contributionWindow`
  (`src/lib/cycle-index.ts:59-99`).
- A cycle page renders either a frozen record from the published
  cycle index or, for a month the rolling snapshot still covers, a
  live view derived from that snapshot. The frozen record wins: "A
  frozen record is what is under review; never replace it with a live
  recompute, even while the rolling window still covers the month"
  (`src/CyclePages.tsx`, render comment in `CyclePage`).
- The page shows four stages — Contribution (the window), Owner
  changes, Approval, Payment. From 2026-11 the second stage is the
  monthly cutoff below; earlier records keep a 14-day Review stage
  ending at `reviewEndsAt` ("From 2026-11, owners change allocations
  until the monthly cutoff instead of a 14-day review (PRD section
  6)", `src/CyclePages.tsx`). The headline amount is the paid
  principal for a paid cycle, else approved, suggested, or projected
  principal by state, and a record whose funding basis is not
  committed says so: "No funding committed for this cycle."
- The archive page ("Payment cycles", `CycleArchivePage`) lists every
  published record sorted by cycle id descending, then project id,
  with project/month/state filters. Both pages flag stale data: a
  snapshot is stale 8 hours after its `generatedAt`
  (`SNAPSHOT_STALE_AFTER_MS = 8 * 60 * 60 * 1_000`,
  `src/lib/use-snapshot.ts:24`), shown as "Cycle history may be
  outdated · updated …".

### How standings are computed

- Home standings ("Top sloperators") read exactly one file,
  `/data/points-summary.json`, through a bounded, schema-validated
  read (`src/HomeStandings.tsx:11-21`). The summary's own validator
  enforces the invariants the table relies on: contributors sorted
  highest first, unique actor ids, `totals.contributors` equal to the
  row count, and the row totals summing to `totals.points`
  (`src/lib/points-summary.ts:13-54`). The component re-sorts by
  total descending with ties broken by actor id, assigns competition
  ranks (equal totals share a rank; the next distinct total takes its
  positional rank), and renders the top 10 rows.
- Per-cycle standings come from `createProjectView`
  (`src/lib/project-view.ts`), which aggregates one project's journal
  events inside the cycle window, subtracts applied Slopbot debits in
  that project and cycle, and keeps the points of payout-excluded
  contributors (the exclusion removes payment, not points). Display
  and allocation order is adjusted weight descending, then score,
  then `compareActors` (case-insensitive login, then login, then id;
  `src/lib/github-actor.ts:61-69`). Ranks are assigned separately on
  score thirds descending with the same shared-rank rule
  (`assignLeaderboardRanks`, `src/lib/leaderboard.ts:559-567`).
- The frozen cycle table renders a contributor's points as
  `(scoreThirds ?? score * 3) * 10` (`src/CyclePages.tsx`,
  `ArchivedCycleLeaderboard`) and shows suggested, approved, or paid
  amounts according to the cycle's phase, with the full three-phase
  history per row.

### The snapshots behind the pages

- The points summary is a build output regenerated from the
  published points history (`scripts/generate-points.ts` reads
  `/data/points.json` and its shards). Live on 2026-11-11:
  `ruleVersion slop-points-v1`, `generatedAt
  2026-11-10T11:02:50.351Z`, 989 contributors, 750,570 points.
- The rolling leaderboard snapshot is a manifest
  (`/data/leaderboard.json`, format `slop-leaderboard-parts-v1`)
  over content-addressed parts; live it declares 34,251,751 bytes
  across 5 parts, and the part sizes sum to exactly that.
  `loadSnapshot` fetches the manifest and parts, validates the
  assembled snapshot, and builds every project view from it
  (`src/lib/use-snapshot.ts:64-145`).
- The cycle index is published at build time by
  `scripts/prepare-site.mjs` running `scripts/sync-cycle-index.ts`,
  which validates Git-backed cycle directories
  (`cycles/<project>/<cycle>/proposal.json` + `source-snapshot.json`)
  and publishes `/data/cycles/index.json` plus per-cycle artifacts
  under `/data/cycles/<projectId>/<cycleId>/`
  (`src/lib/cycle-index.ts:781,993`). At the pinned commit the
  production `cycles/` root holds only its README — "New monthly
  allocations live in D1" (`cycles/README.md`) — and the live index
  fetched for this packet contains **0 cycle records**
  (`generatedAt 2026-11-10T11:02:16.110Z`, already past the 8-hour
  stale threshold at check time). So today the archive has nothing
  frozen to show; cycle pages render from the live snapshot view.
- A frozen record's shape is still checkable from the format's test
  fixtures (upstream `tests/fixtures/history/cycles/`): the eliza
  2026-09 proposal fixture has the calendar-month window
  2026-09-01 → 2026-10-01, a review end exactly 14 days after its
  last material change, a 64-hex source snapshot digest, and 41
  allocations in `proposed` status. This is a format fixture, not
  the production record of that month.

### The automatic monthly payment flow

- Owner side (`src/AutomaticMonthlyPayment.tsx`): the component is
  the vault owner's on-chain authorization switch. Its own summary:
  "Commits each month's awards after the month ends (UTC), up to the
  monthly amount. Only the vault owner can change it." The owner
  connects the vault owner wallet, reviews current versus target
  setting (enabled flag plus monthly cap in asset base units), signs
  one transaction (EVM or Solana), and the UI reports the setting as
  changed only after checking it against finalized chain state.
  Signing moves no funds; turning it off means "no new monthly
  awards are committed. Committed awards stay committed."
- Server side (`backend/payments/README.md`, "Monthly allocations
  and the automatic monthly coordinator"): (1) Proposal — the
  trusted `monthly-rewards.yml` workflow runs on the first three
  days of a month, freezes the complete ledger of the closed UTC
  month, and writes one proposal per active, verified monthly-pool
  project with a registered vault and a positive monthly amount:
  per-contributor integer base units by largest remainder of the
  shared pool, plus any committed review line. A month's proposal is
  written once; unfunded projects get none. (2) Private changes —
  the owner, steward, or a repository admin adjusts amounts through
  the payments API; the month's total never exceeds its monthly
  amount, every change is an append-only D1 row kept only for
  disputes and reconciliation, and no route returns it.
  `POST .../monthly-settings` toggles the automatic default. (3)
  Execution snapshot — an explicit finalize call, or the payments
  Worker's coordinator at the cutoff, freezes the allocations into
  the month's single `monthly_payment_runs` row; a frozen month
  accepts no further change. The cutoff comes from
  `MONTHLY_PAYMENT_SCHEDULE`: owner decision D1 (24 October 2026)
  sets `{"firstPeriod":"2026-11","cutoffSecondsAfterPeriodEnd":259200}`
  — calendar UTC months from November 2026, cut off 72 hours after
  the month ends; unset, nothing freezes automatically. The public
  pages mirror the same schedule as `PRD_MONTHLY_SCHEDULE`
  (`src/lib/payments/monthly-allocation.ts:42-46`), kept equal by a
  unit test, and `monthlyCutoff` returns null before 2026-11. (4)
  Obligations — created once per positive award, only when a vault
  snapshot newer than 30 minutes shows the finalized free balance
  covering the month plus all earlier unreserved obligations of that
  vault; accounts under an active moderator ban are excluded and the
  frozen snapshot is kept. (5) Authorization and execution — the
  attester signs each funded month's allocation root; publication is
  not a reservation or payment, and an executor still submits the
  bounded commitment and reconciles finalized results.

### What is public and what lives only on the server

| Data | Where it lives |
| --- | --- |
| All-time contributor totals | Public: `/data/points-summary.json` |
| Rolling journal-derived views | Public: `/data/leaderboard.json` manifest + parts |
| Frozen cycle records (when published) | Public: `/data/cycles/index.json` + per-cycle artifacts |
| Vault monthly setting (enabled, cap) | Public: finalized on-chain state, read by the owner UI |
| Latest signed monthly authorization | Public API: returns the attempt and its publication time, no signer/RPC call |
| Monthly proposals, allocation changes, runs, obligations, exclusions | Server only: private D1 records; the change rows have no public route and no public reason |
| `MONTHLY_PAYMENT_SCHEDULE` value | Server configuration; the site mirrors it as `PRD_MONTHLY_SCHEDULE` for display |

## Verification

- `python3 scripts/verify-cycle-standings.py --proposal <upstream
  fixture proposal.json>` — run live on 2026-11-11 (check time
  2026-11-11T11:57:08Z): **ALL CHECKS PASSED**. It verified the live
  summary's internal consistency (989 rows, sum 750,570, published
  order non-increasing, unique ids, all totals multiples of 10),
  recomputed the home standings (top 10: lalalune 256,610;
  NubsCarson 61,750; ss251 47,240; hermesagent270-commits 36,870;
  attentionhead 27,100; 0xSolace 25,720; WalkCrypto 19,380;
  standujar 17,630; Chihyunpark1 16,930; shawkkkkk 9,000 — no tie
  straddles the top-10 boundary, #11 has 8,610), read the live cycle
  index (0 records, stale threshold passed), summed the snapshot
  manifest's parts to its declared 34,251,751 bytes, recomputed the
  calendar arithmetic (2026-11 window; cutoff 2026-12-04T00:00:00Z;
  no cutoff for 2026-10), and validated the fixture proposal's
  window, 14-day review end, and digest format.
- `python3 -m pytest tests/` — 3 new tests over local fixtures
  (shared-rank ties, a wrong-total failure case, the proposal window
  and review arithmetic) plus the existing 4 selector tests, all
  passing (run by direct function invocation in this environment,
  which has no pytest; the repo CI installs it).

## Notes

- Limits: the rolling snapshot's 34 MB of parts were not
  reassembled, so the per-cycle live view was verified by its source
  rules plus the summary-side recompute, not by re-running
  `createProjectView` end to end. Because the live cycle index holds
  no records yet, the frozen-table arithmetic was checked against
  the format fixture, not against a live frozen cycle; the window
  check for real index entries runs in the checker whenever records
  exist.
- Boundaries with neighbouring packets: the closed-cycle evidence
  gate for reward proposals (open PR #37) covers
  `src/lib/reward-cycle.ts` eligibility, not the pages; the points
  rules themselves are PR #23 and the project registry and its
  leaderboard are PR #42. This packet cites the ordering rule only
  from the cycle/standings side.
- Nothing here states whether any particular month was proposed,
  approved, or paid; those states are exactly the server-side
  records above, and the one dated example used is a test fixture.

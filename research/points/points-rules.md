# Points rules — how points are earned and what changes the balance

## Target

The points rules in the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT licensed), pinned at commit
`7dc83b504627c70eb6d1f0d1950b40aad3006bf8`:

- `src/PointsRules.tsx` (the rules rendered on the points page)
- `src/lib/score-records.ts` (`SCORE_TIERS`)
- `src/lib/points.ts` (`POINTS_PER_THIRD`)
- `src/lib/penalty-guide.ts` and `workers/slopbot/penalties.ts`
  (the published penalty table)
- `protocol/points-v1.md` (the canonical points protocol)
- `backend/points/handler.ts`, `backend/points/disputes.ts`,
  `backend/points/x.ts` (membership, disputes, X connections)

Cross-checked against the live points page at
`https://slop.cash/points` on 2026-11-11.

## Claim

Accepted work earns tiered points from 10 (micro) to 750 (exceptional) at
10 points per score-third, reviews earn 10–240 points by depth, each
verified payout earns 25 recognition points per project and finalized
month, balances never decay and nothing multiplies points, participation
awards (welcome 5, X connection 10) ended on 2026-10-24, Slopbot
penalties debit 0–240 points by category, and only the recipient can
dispute a points record, within 7 days.

## Evidence

### 1. Contribution tiers — 10 points per score-third

`SCORE_TIERS` in `src/lib/score-records.ts` stores thirds, and
`POINTS_PER_THIRD` in `src/lib/points.ts:370` is `10`.
`formatPointsFromThirds` (`src/Presentation.tsx:526`) renders
`thirds * POINTS_PER_THIRD`. `src/PointsRules.tsx` renders exactly this
table on the points page, and the live page shows the same numbers.

| Tier | Thirds | Points |
| --- | --- | --- |
| Micro | 1 | 10 |
| Small | 3 | 30 |
| Medium | 9 | 90 |
| Large | 24 | 240 |
| XL | 45 | 450 |
| Exceptional | 75 | 750 |

Source: `src/lib/score-records.ts` (`SCORE_TIERS`), `src/lib/points.ts:370`,
`protocol/points-v1.md` ("Tiered accepted work earns ten points per
unweighted score-third: micro 10, small 30, medium 90, large 240, XL 450,
exceptional 750").

### 2. Review points

| Review | Points |
| --- | --- |
| Triage | 10 |
| Standard | 30 |
| Deep | 90 |
| Specialist | 240 |
| Ordinary review (only as the one outcome review of its PR, from 2026-10-01) | 10 |

Source: `protocol/points-v1.md` ("Eligible standard reviews earn 30;
from 2026-10-01 an ordinary review earns 10 only as the one outcome
review of its pull request; reviewed triage, deep, and specialist reviews
earn 10, 90, and 240"); live page: "Useful reviews: triage 10 ·
standard 30 · deep 90 · specialist 240 points."

One work unit earns once: "A logical accepted work unit earns once.
Ordinary reviews do not also earn an evaluated review award on the same
PR. Bots, self-review, unaccepted work and unreviewed external activity
do not earn contribution points." (`protocol/points-v1.md`).

### 3. Provisional and payout-recognition points

- Historical merged PRs initially receive **10 provisional points**
  each. A Score v2 merge from 2026-10-01 without a ratified tier is
  provisional small credit: **30 provisional points**.
  (`protocol/points-v1.md`; live page: "Merged PR before scoring
  began 10 each".)
- Each verified finalized payout earns the recipient **25 points per
  project and finalized monthly payout cycle** with positive paid
  principal. Dollar size, fee size, separate reward lines, and
  transaction splitting never multiply this award.
  (`protocol/points-v1.md`; live page: "Verified payout 25 per project
  and month".)

### 4. No decay, no multipliers, no cash value

- "Points have no monetary value and cannot be transferred or redeemed."
  (`protocol/points-v1.md`; live page repeats it.)
- "Token usage, cost, model, signed-receipt weight, wallet state, and
  payment never multiply points." (`protocol/points-v1.md`.)
- "Recorded totals persist between months, subject to explicit
  corrections." No decay rule exists in any reviewed source.
- Monthly earned-point standings use UTC occurrence dates, include
  verified payout points, exclude historical welcome and X connection
  points, and give equal totals equal ranks. Badges grant no points.

### 5. Participation awards ended 2026-10-24

- Joining with a GitHub account earned **5 welcome points once** until
  24 October 2026; it now earns none. The first verified X connection
  earned **10 points once** per GitHub account; connections now earn
  none. Awards recorded before that date stay unchanged.
  (`protocol/points-v1.md`.)
- Enforced in code: `PARTICIPATION_POINTS_END =
  "2026-10-24T00:00:00.000Z"` in `backend/points/handler.ts:87`; the
  points API reports a welcome award only for a membership whose
  immutable `joined_at` is before that instant, and an X award only
  when its immutable `awarded_at` is before it.
- X connections today grant no points:
  `backend/points/x.ts:76` — "Connections grant no points."

### 6. Penalties — the published table

Debits are Slop Score thirds shown in points (×10). Derived from
`PENALTY_TABLE` in `workers/slopbot/penalties.ts`; the guide renders
them via `PENALTY_ROWS` in `src/lib/penalty-guide.ts` so it cannot
drift from the bot.

| Slopbot category | Action | Debit (points) |
| --- | --- | --- |
| Spam | Close | 30 |
| Scam or malicious | Close; moderator reviews the account | 240 |
| Clear violation of a quoted project rule (busywork, gaming) | Close | 10 |
| Low quality | Close (closure-eligible authors only) | 0 |
| Duplicate | Close | 0 |
| Out of scope | Label only | 0 |

`empty` and `missing_evidence` carry no debit and are not published
rows. The applied debit is capped by that month's deduplicated
accepted-work Points, and only an explicit identity-matched Slopbot
reversal restores a debit. (`protocol/points-v1.md`.)

### 7. Disputes — only the recipient, within 7 days

- A dispute targets one retained, immutable points revision:
  `POST /api/v1/points/disputes` with `revisionId` (64-hex) and a
  reason (≤ 4000 characters). Only the recipient can dispute their own
  record; anyone else gets 403.
  (`backend/points/disputes.ts`.)
- The dispute is due `APPEAL_RESOLUTION_DAYS` = **7** days after
  opening (`workers/slopbot/appeals.ts:13`). After escalation, an
  independent moderator decides `uphold` or `deny` with a reason.
- Re-disputing the same record returns 409 `already_submitted`;
  disputing a superseded record returns 409 `superseded`.
- "Contest an award through the project's GitHub review process; never
  put private security evidence in a public appeal."
  (`protocol/points-v1.md`.)

### 8. Sessions and account closure (what else changes a balance view)

- Points web sessions are one-hour HttpOnly, Secure, SameSite=Strict
  sessions; sign-out invalidates the session and never resets a
  historical welcome award. (`protocol/points-v1.md`.)
- A member can close the account (`POST /api/v1/points/account/close`);
  only a sign-in that sends `reopen: true` opens it again.
  (`protocol/points-v1.md`.)

## Verification

Re-checked 2026-11-11 against the pinned commit
`7dc83b504627c70eb6d1f0d1950b40aad3006bf8` of
`SlopDotCash/slopdotcash`:

1. Tiers: `SCORE_TIERS` in `src/lib/score-records.ts` is
   `{micro: 1, small: 3, medium: 9, large: 24, xl: 45, exceptional: 75}`;
   `POINTS_PER_THIRD` in `src/lib/points.ts:370` is `10`; 1×10=10,
   3×10=30, 9×10=90, 24×10=240, 45×10=450, 75×10=750.
2. Penalties: `PENALTY_TABLE` in `workers/slopbot/penalties.ts` reads
   `spam: {close, 3}`, `scam: {close, 24, moderatorReview: true}`,
   `low_quality`/`duplicate`/`empty`/`missing_evidence`: 0,
   `out_of_scope: {label, 0}`, `busywork`/`gaming`: quoted-rule 1 third.
3. Disputes: `APPEAL_RESOLUTION_DAYS = 7` in
   `workers/slopbot/appeals.ts:13`; the 403/409 rules above are in
   `backend/points/disputes.ts`.
4. Participation end: `PARTICIPATION_POINTS_END =
   "2026-10-24T00:00:00.000Z"` in `backend/points/handler.ts:87`.
5. Live page cross-check: `https://slop.cash/points` shows the same
   tier table (10/30/90/240/450/750), "Useful reviews: triage 10 ·
   standard 30 · deep 90 · specialist 240 points", "Merged PR before
   scoring began 10 each", and "Verified payout 25 per project and
   month".

To re-run: fetch the files above at the pinned commit from
`raw.githubusercontent.com/SlopDotCash/slopdotcash/<commit>/…` and
compare the quoted values; open `https://slop.cash/points` and compare
the displayed tables.

## Notes

- This packet summarizes the rules; it does not change any rule, run
  the points backend, or inspect production D1 data. The dispute flow
  was verified by reading `backend/points/disputes.ts` only — no dispute
  was filed against the live service.
- No decay rule was found in `protocol/points-v1.md`,
  `backend/points/`, or the points page. If a decay rule exists
  elsewhere in the codebase, it is outside the files Issue #17 names.
- Scope: Issue #17 only. The other points-adjacent areas (payout
  mechanics, referral accrual, worker triggers) are separate issues
  and are not covered here.

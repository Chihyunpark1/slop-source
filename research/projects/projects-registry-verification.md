# Projects — the registry, its publication gates, and its live risk flags

## Target

Issue #1: the Projects system of the SLOPCASH platform — how projects
are proposed, listed, ranked, set up, and flagged for risk. This packet
covers the system as a whole and verifies its live published state; the
proposal form's field-by-field list is issue #16 and is not repeated
here.

Studied in:

- The public registry endpoints, read live on 2026-11-11:
  `GET https://slop.cash/.well-known/slop/projects.json`,
  `GET https://slop.cash/api/v1/projects`, and
  `GET https://slop.cash/api/v1/projects/<project_id>` for every
  project the discovery index names.
- The public SLOPCASH codebase (`SlopDotCash/slopdotcash`, MIT) pinned
  at development commit
  `ced75d782d5836f60d84f46d50604f75a5852438`: `backend/projects/`
  (README, `handler.ts`, `setup.ts`, `skill-publication.ts`,
  `contracts.ts`), `src/ProjectProposalPage.tsx`,
  `src/ProjectSetupStatus.tsx`, `src/ProjectLeaderboard.tsx`,
  `src/ProjectRiskFlag.tsx`, `src/lib/project-view.ts`,
  `src/lib/leaderboard.ts`, and `backend/vetting/flags.ts`.

## Claim

The public registry is a gated publication system, not a list a
project joins by pull request: on 2026-11-11 it held 32 projects, the
discovery index exposed exactly the 18 that are active,
skill-publishing and scan-cleared, and across those 18 the money and
risk signals are uniform in a specific way — payments are disabled and
committed funding is zero for every project, and receipt-policy
activation matches authority verification project for project (6
projects verified with an active receipt policy; the other 12
unverified with a pending one, each showing the same
`missing-repository-proof` state that the proposal form writes into a
new project's first revision).

## Evidence

### 1. The registry and its public surface

- The D1 database `slop-private` is the only project inventory, and
  "Projects are added on slop.cash, not by pull request"
  (`backend/projects/README.md`, lines 3–4). The stored history is
  append-only: `project_revisions` triggers refuse update and delete,
  and the `projects` table is a pointer to the newest revision (same
  README, "Tables"). The API contract version is `project-registry-v1`
  (`backend/projects/contracts.ts`, line 12).
- Public, unauthenticated reads: the project list
  (`GET /api/v1/projects`, manifests plus a `restrictions` array), one
  project (`GET /api/v1/projects/<id>`), the full revision history
  with SHA-256 digests (`GET /api/v1/project-revisions`), the
  discovery index (`/.well-known/slop/projects.json`, described as
  "Repository-to-project routing for every project that publishes
  skills", `backend/projects/README.md` line 78), and per-project
  artifacts such as `/projects/<id>/terms.json` and the generated
  skills (same README, "Routes" and the artifact table).
- The detail response is assembled in `readPublicProject`
  (`backend/projects/handler.ts`, lines 2794–2840): schema version
  `"1"`, the current manifest, its revision number and manifest
  SHA-256, and two computed fields — `vetting` (the project's scan
  clearance summary) and `skillsPublished`. A restricted project
  answers HTTP 410 with a public restriction summary instead
  (line 2812); a retired project answers 404.

### 2. How a project gets in: proposal, creation, setup, activation

- There is no routine admin approval. A signed-in owner submits the
  proposal form at `/projects/new`; the submit calls `createProject`
  (`src/ProjectProposalPage.tsx`, line 1349), and
  `POST /api/v1/projects` "Creates a paused project at once … queues
  its first scan and returns the setup status"
  (`backend/projects/README.md`, "Routes"). Applications filed before
  self-service setup are not re-entered or admin-decided anymore: the
  applicant publishes a stored application, which becomes revision 1
  of a paused project (`backend/projects/contracts.ts`,
  `publishApplication`; README, "Migration of stored applications",
  line 178).
- Before creation, the manifest is checked against public GitHub
  facts: the repository and steward identities must match GitHub
  exactly or the request is refused with `422 invalid_manifest`
  (README, "Self-service setup", line 86; the check itself is
  `repositoryControl` in `backend/projects/setup.ts`). Those facts
  never grant authority — the one authority path is the Slopbot
  installation read, which must show write, maintain or admin access
  for the owner; without an installation the request fails with
  `409 slopbot_required`, with less than write access with
  `403 authority_required` (README, "Self-service setup").
- A new project must start as "a paused, unverified, unfunded
  community project with one repository, payments disabled" and
  generated skills from the canonical templates; steward, authority,
  terms, status, listing tier and money fields are refused in owner
  writes (`422 owner_field_restricted`) and arrive only through later
  revisions (README, "Trust rules").
- Setup is one derived status per project with three checks —
  Slopbot installation, GitHub authority, security scan — plus
  funding reported separately, because "a project works without it"
  (`backend/projects/setup.ts`, lines 1–9). The owner-facing states
  are Ready, Action needed, Waiting for the security scan,
  Unavailable, and Closed to contributors
  (`src/ProjectSetupStatus.tsx`, `HEADINGS`). The next action is the
  first unmet check in setup order: installation, then authority,
  then the scan (`projectSetupStatus` in `backend/projects/setup.ts`).
  Activation happens when the owner runs the setup check and every
  check passes: `POST /api/v1/project-setup/<id>/check` "activates a
  project that passes" (README, "Routes" and "Activation").

### 3. The publication gates, in code

A project appears in the discovery index only if it passes every gate
in `discovery()` (`backend/projects/skill-publication.ts`,
lines 182–219):

- `project.status === "active"`,
- the project is listed (not restricted and not retired),
- its manifest publishes generated skills
  (`publishesGeneratedSkills`),
- and its vetting clearance for the current revision is `"cleared"`.

The index emits one entry per repository in the manifest, with exactly
seven fields per entry: `project_id`, `project_url`, `repository`,
`review_skill`, `review_skill_manifest`, `skill`, `skill_source`,
under `"schemaVersion": "1"`. The detail endpoint applies the same
rule per project: `skillsPublished` is
`publishesGeneratedSkills(manifest) && vetting.state === "cleared"`
(`backend/projects/handler.ts`, line 2830). A site page reads the
registry from `GET /api/v1/projects` when it loads, so a created or
revised project "appears within a minute, without a build" (README,
"Publication", line 417); public reads are edge-cached with a
30-second TTL keyed by an enforcement generation counter (README,
"Caching").

### 4. The live registry on 2026-11-11

`scripts/verify-projects-registry.py` fetched the three public
endpoints and every detail record, aggregated the published fields,
and cross-checked that discovery and the detail records agree. Full
output is quoted under Verification. The headline numbers:

- Discovery index: 18 entries, schema `"1"`. Registry list: 32
  projects. The 14 projects in the list but not in discovery are all
  `paused` (12 community tier, 2 retired tier: `heir-elements-sdk`,
  `pumpfun-source`), which is exactly what the gates in section 3
  predict: discovery exposes only active, cleared,
  skill-publishing projects. No project is in discovery but missing
  from the list, and the list published no restrictions at fetch
  time.
- All 18 discovered projects: status `active`, vetting `cleared`,
  `skillsPublished` true, exactly one repository each, discovery
  repository identical to the detail record's repository (18/18
  cross-checks passed).

| Project | Status | Tier | Authority | Terms | Receipt policy | Funding | Committed | Payment | Vetting | Skills |
|---|---|---|---|---|---|---|---|---|---|---|
| asi | active | community | verified | 2026-08-20.1 | active | pledged | 0 | disabled | cleared | True |
| bountix | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| bruhos | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| canonry | active | community | verified | 2026-10-02.1 | active | pledged | 0 | disabled | cleared | True |
| delta-star | active | featured | verified | 2026-08-23.1 | active | external-opportunity | 0 | disabled | cleared | True |
| eliza | active | featured | verified | 2026-08-18.1 | active | pledged | 0 | disabled | cleared | True |
| feed | active | community | verified | 2026-11-01.1 | active | pledged | 0 | disabled | cleared | True |
| hyperliquid-source | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| inscrib3-wallet | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| monna-agent-permission-diff | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| ohio-project-south | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| oldest | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| orbio-contracts | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| slop-cash-reverse-engineering | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| slopdotcash | active | featured | verified | 2026-10-11.1 | active | pledged | 0 | disabled | cleared | True |
| thenetwork | active | featured | unverified (missing-repository-proof) | 2026-10-11.1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| umia-protocol | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |
| visual-strategy-canvas | active | community | unverified (missing-repository-proof) | draft-1 | pending-authority-activation | pledged | 0 | disabled | cleared | True |

Field counts across the 18 detail records, from the checker output:

- Listing tier: community 14, featured 4 (delta-star, eliza,
  slopdotcash, thenetwork).
- Authority: verified 6 (asi, canonry, delta-star, eliza, feed,
  slopdotcash); unverified 12, every one with reason
  `missing-repository-proof` and a null proof.
- Receipt policy: active 6 — the same six projects as verified
  authority; pending-authority-activation 12 — the same twelve as
  unverified. The two sets match exactly.
- Terms revisions: `draft-1` for 11 projects; dated revisions for 7.
  `thenetwork` is the separating case: it carries a dated terms
  revision (`2026-10-11.1`) yet is still unverified with a pending
  receipt policy, so the receipt policy tracks authority
  verification, not the terms date.
- Funding: `pledged` for 17, `external-opportunity` for 1
  (delta-star); `committedMinor` is `"0"` for all 18 and
  `paymentMode` is `disabled` for all 18 — no discovered project has
  committed funding or enabled payments.
- Displayed monthly pool caps range from `$0` (8 projects) through
  $250 (asi), $500 (feed, thenetwork) and $1,000 (bruhos, eliza,
  slopdotcash) to token-denominated caps of 10,000,000 EPYH
  (hyperliquid-source) and 30,000,000 RSLOP
  (slop-cash-reverse-engineering); delta-star shows
  `$0 platform pool`. A cap is a ceiling the project declares, not
  committed money — committed is separately zero everywhere, above.
- Stewards: individual 8, organization 7, dao 2 (both naming
  SlopDotCash), collective 1 (delta-star).
- The `slopbot` block is empty in 10 of the 18 records. Where
  `automaticClosure` is present it is true for 7 projects (bountix,
  bruhos, canonry, inscrib3-wallet, ohio-project-south, oldest,
  slop-cash-reverse-engineering) and false for 1
  (hyperliquid-source).

### 5. The leaderboard: what ranks a project page

Each project page shows one leaderboard per reward cycle (a UTC
calendar month), rendered by `CycleAllocation` in
`src/ProjectLeaderboard.tsx`:

- Rows are contributors with accepted work in that cycle for the
  project's repositories. Rank is a competition rank (equal scores
  share a rank) assigned on score thirds in descending order:
  leaders are sorted by `scoreThirds` descending in
  `src/lib/project-view.ts` (lines 646–656) and ranked by
  `assignLeaderboardRanks` in `src/lib/leaderboard.ts`
  (lines 559–567). The displayed points are the score thirds
  converted by `formatPointsFromThirds`, with review points itemized
  and any Slopbot penalty shown as a deduction on the row.
- The share column is a projection, not a payment: for a monthly
  pool it is the contributor's adjusted weight as a percentage of
  the pool (or the simulated amount when the pool is funded), for
  an external prize it is the projected share, and rows for owners,
  funded employees and related parties are labelled "Excluded from
  payout" instead (`PAYOUT_EXCLUSION_LABELS` and `RewardValue` in
  `src/ProjectLeaderboard.tsx`; the exclusion list itself is part of
  the manifest's `reward.payoutExclusions`, README "Self-service
  setup"). An unfunded pool is announced as such
  (`UNFUNDED_POOL_HEADLINE`) and shares are shown as weight only.
- "No accepted work this month yet." is the empty state; the board
  is a projection of the points ledger for the cycle, and the
  registry manifest supplies the reward terms it is projected
  against.

### 6. Risk flags: published signals and the flag mechanism

Two different things carry the word "risk" in this system.

Published signals in every project record (all values above are from
the live fetch): `authority.state` with its `reason` and null
`proof`; `terms.receiptPolicy.state`; `reward.fundingState`
(`pledged` vs committed) with `committedMinor` and `paymentMode`;
the `vetting` summary; and enforcement state — a restricted project
disappears from discovery, its detail endpoint answers HTTP 410, and
the list endpoint publishes its restriction (none were published at
fetch time).

The contributor flag mechanism (`src/ProjectRiskFlag.tsx`, header
comment lines 1–7; `backend/vetting/flags.ts`):

- A signed-in member flags a project for malicious code or injection
  risk in one of six categories: wallet-drainer, credential-theft,
  secret-exfiltration, unsafe-execution, prompt-injection, other
  (`CATEGORY_LABELS` in `src/ProjectRiskFlag.tsx`; `FLAG_CATEGORIES`
  in `backend/vetting/flags.ts`, line 57).
- Eligibility: a GitHub account at least 30 days old and one accepted
  Slop contribution. Evidence is required (20–4,000 characters) with
  an optional github.com link; the form warns "Do not paste
  secrets."
- A flag counts for 90 days (`FLAG_ACTIVE_LIFETIME_MS` =
  7,776,000,000 ms, `backend/vetting/flags.ts` line 64). Two
  distinct members' active flags pause the project at once: the
  second distinct active flag appends a `quarantine` enforcement
  record whose issuer is `contributor-flags`, and a clean fresh scan
  reinstates it (`backend/projects/README.md`, lines 396–399). A
  member sees only their own flag; withdrawing a flag does not lift
  an existing pause.

### 7. Public data vs server-only data

Public (no session): the discovery index, the project list and
detail records, the full revision history with digests,
`/projects/<id>/terms.json`, generated skill artifacts, and the
public restriction summaries (project id, state, appeal state, start
time — no reason or evidence).

Server-only or session-scoped: the registry database itself and its
application, enforcement and revision stores beyond the public
projections; the setup status and its installation/authority/scan
check details (owner session); stored applications (the applicant's
own session); a member's flag status (their own flag only);
moderation reasons and evidence references; and every admin route.
The proposal form's draft is kept client-side and in the account's
stored applications — a draft is not a registry record until it is
submitted or published.

## Verification

Checker added by this packet: `scripts/verify-projects-registry.py`
(standard library only, read-only GETs of the three public
endpoints). Run live:

```text
$ python3 scripts/verify-projects-registry.py
Discovery entries (projects.json): 18
Registry list entries (GET /api/v1/projects): 32
In the registry list but not in discovery (no published skills):
  ['beam', 'darling-arm64', 'delta-git', 'eliza-valhallaos', 'fly-ai',
   'fortune-launchpad', 'gocode', 'heir-elements-sdk', 'nurosos',
   'payzcode-ai', 'pumpfun-source', 'slopdotcash1', 'toon-plugins',
   'unbrowse']
Statuses of those list-only projects: paused=14
In discovery but not in the registry list: none
Restrictions published by the list endpoint: none
...
- status: active=18
- listingTier: community=14, featured=4
- authorityState: unverified=12, verified=6
- authorityReason: None=6, missing-repository-proof=12
- receiptPolicyState: active=6, pending-authority-activation=12
- fundingState: external-opportunity=1, pledged=17
- paymentMode: disabled=18
- vettingState: cleared=18
- skillsPublished: True=18
Projects with committedMinor other than 0: none
Projects with authority.state verified:
  ['asi', 'canonry', 'delta-star', 'eliza', 'feed', 'slopdotcash']
ALL CROSS-CHECKS PASSED
```

(The two tables in section 4 are the checker's full table output,
reformatted only to fit this page.)

What was checked:

- Every cross-check the script performs passed on the live registry:
  discovery schema is `"1"`; each detail record's id matches its
  discovery entry; each detail record's primary repository matches
  the discovery repository (18/18); the verified-authority set and
  the active-receipt-policy set are identical (read off the
  aggregated table and the field counts).
- The same aggregation was re-run offline from the saved responses
  (`--snapshot` mode) with the identical result, and the script's
  aggregation is covered by `tests/test_verify_projects_registry.py`
  (consistent snapshot passes; a repository mismatch is reported
  with exit 1; an HTTP 410 detail is reported as a restricted row,
  not a failure). Full test run: `python3 -m pytest tests/ -q` →
  7 passed (4 existing selector tests + 3 new).
- The birth-state cross-check: the proposal form builds a new
  manifest with `authority.state` `"unverified"`, reason
  `"missing-repository-proof"`, `terms.revision` `"draft-1"` and
  `receiptPolicy.state` `"pending-authority-activation"`
  (`src/ProjectProposalPage.tsx`, lines 1193–1206) — exactly the
  values 11–12 of the 18 live records still carry.
- Code citations were read at the pinned commit
  `ced75d782d5836f60d84f46d50604f75a5852438` of
  `SlopDotCash/slopdotcash` (the development tip at fetch time);
  line numbers above are from that commit.

## Notes

- Point in time: registry counts and field values are the state at
  the 2026-11-11 fetch. Owners can publish revisions at any time
  and public reads are cached for about 30 seconds, so a re-run may
  legitimately differ in detail; the gates and flows in sections
  2–3 are the durable part.
- Session-scoped surfaces (setup checks, stored applications, flag
  status) cannot be read without an account session, so those flows
  are documented from the public source code, not from live private
  responses. No session was used and no private data was collected
  for this packet.
- The proposal form's field list, with required/optional and
  validation per field, is issue #16's packet; this packet cites
  the form only where it writes registry-visible state.
- Related packets: issue #2 (points rules) covers the ledger the
  leaderboard projects from; issue #12 covers the token. Nothing in
  this packet repeats them.

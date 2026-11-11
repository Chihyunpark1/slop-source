# Identity & profiles — ID-keyed profiles on a sessionless public surface

## Target

Issue #7: the identity and profile features of the public SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT), pinned at development commit
`ced75d782d5836f60d84f46d50604f75a5852438`:

- `src/ProfilePage.tsx`, `src/Profiles.tsx`, `src/Points.tsx`
  (profile page, identity directory, membership reads)
- `src/lib/github-actor.ts`, `src/lib/profiles.ts`,
  `src/lib/cycle-index.ts`, `src/lib/use-snapshot.ts`
- `backend/identity-assertion.ts`, `backend/points/handler.ts`
  (assertion consume, join/session, public member views)
- `workers/identity/` (the identity Worker: OAuth flow and assertions)
- `backend/trace/handler.ts` (wallet-claim reads and creation)

Live public surface checked on 2026-11-11:
`https://slop.cash/data/profiles.json`, `/data/leaderboard.json`,
`/data/cycles/index.json`, `https://slop.cash/api/v1/points/people`,
`/api/v1/points/member?login=…`, and
`https://api.slop.cash/api/v1/wallet-claims/actors/<id>/current`.
The worked example throughout is this packet author's own public
account (`dd12m54`, numeric GitHub ID `341532112`), so no third party's
record is reproduced.

## Claim

A Slop contributor profile is keyed by the immutable GitHub actor
identity — membership and the web session are keyed by the numeric
GitHub user ID, with the GitHub node ID stored as the actor key at
first join — so the login in a profile URL is only a display hint that
several public records must corroborate before the page renders, and
everything the public profile page shows (per-repository PR counts,
project standings, penalty history, and the current wallet claim) is
served from sessionless public records, while the session token,
wallet-claim creation, and the identity Worker's flow state stay
server-side.

## Evidence

All line references are to the pinned commit above. Behavioral claims
about the live site are backed by the checker added in this PR
(`scripts/verify-identity-profile.py`); its observed output is quoted
in Verification.

### 1. Identity: GitHub login in, ID-keyed session out

- Sign-in runs through a dedicated identity Worker
  (`https://identity.slop.cash`, `workers/identity/contracts.ts`).
  `/v1/oauth/start` creates a flow record holding only hashes (state
  hash, poll-capability hash) plus an encrypted PKCE verifier; the
  browser is sent to `github.com/login/oauth/authorize`
  (`workers/identity/handler.ts`, `authorizeBrowser`). The callback
  (`oauthCallback`) records the numeric `githubActorId`, the login,
  and the node ID on the flow; the browser polls `/v1/oauth/poll`
  (poll-after 2 s). Flow TTL is 5 minutes.
- The Worker then issues a **one-time assertion**: stored as a token
  hash, bound to one audience (`slop-points-web` for the site, or
  `private-trace-api`), with a 90-second TTL
  (`contracts.ts`: `ASSERTION_TTL_SECONDS = 90`); consumption stamps
  `consumedAt`, so an assertion is spent on first use.
- The points backend consumes it server-to-server
  (`backend/identity-assertion.ts`): POST
  `https://identity.internal/v1/assertions/consume` with the audience;
  401 maps to "expired", a wrong audience or a non-numeric actor ID
  maps to "invalid". The accepted identity is the numeric
  `githubActorId`, the login, and the node ID.
- Joining (`POST /api/v1/points/join` in `backend/points/handler.ts`)
  keys membership by the **numeric GitHub ID**: a returning member is
  found by `github_id`, and the stored `actor_id` — the node ID
  recorded at first join — is never rewritten ("actor_id and
  github_id are immutable", handler comment citing PRD section 3).
  The session is a random 32-byte token of which only the SHA-256
  hash is stored (`points_sessions`), with a 1-hour expiry and a
  3600-second cookie. A closed account is not revived by an ordinary
  sign-in: join answers 409 `account_closed` unless the request
  explicitly asks to reopen.
- The two ID forms are interchangeable without a GitHub call:
  `githubUserIdFromNodeId` (`src/lib/github-actor.ts`) decodes both
  the legacy base64 `04:User<id>` node ID and the current `U_`
  MessagePack `[0, id]` form, accepting only the canonical spelling
  GitHub emits. Its comment states the point of the design: "The ID
  survives renames and deleted accounts, so no GitHub request is
  needed to join records by actor."

### 2. The profile page: fields and where each comes from

`src/ProfilePage.tsx` renders nothing identity-bearing from the URL
alone. Until the public records name the login, the page shows an
"unverified identity" heading (the typed login, no GitHub link) or a
"No Slop contributor with this login" notice. The actor is selected
by `currentProfileActor`, which cross-checks the signed-in session
actor, the snapshot leaders, the project views, the membership
record, and the identity directory — and **any** source can veto: if
the same ID appears under a different login, or the same login under
a different ID, the candidate is rejected. The directory alone can
resolve an inactive actor, but only when exactly one candidate
remains, and it "cannot override a known rename".

What a rendered profile shows, and its source:

| Field on the page | Source (all sessionless) |
|---|---|
| Name, avatar, GitHub link | The resolved actor record (ID, login, avatar URL) |
| Per-repository PR counts (merged / open / closed) and activity | `/data/profiles.json`, the identity directory: `people[]` records of `{id, login, avatarUrl, repositories[{repository, merged, open, closed}]}` (`src/lib/profiles.ts`), fetched and schema-checked by `useProfiles` in `src/Profiles.tsx` |
| Points, membership, welcome and social points | Public member views of the points backend (below) |
| Projects section: per-project accepted-work points and share bar | Project views computed from `/data/leaderboard.json` (`src/lib/use-snapshot.ts`) |
| Penalty history (project, PR link, category, month, debit, applied amount) | The same snapshot's `penalties` array, filtered by actor ID (`ProfilePage.tsx`) |
| Contribution history by cycle | The cycle index (`/data/cycles/index.json` + per-cycle files): each cycle's contributors, keyed by actor ID (`src/lib/cycle-index.ts`) |
| Current wallet (shortened address + link) | The wallet-claim API, section 3; falls back to the wallet recorded for the actor in a past cycle's contributor record ("Past wallet") |

Two public member views feed the page, both readable with no session
through the site's own origin:

- `GET /api/v1/points/people` — only members flagged public
  (`m.public=1` in `backend/points/handler.ts`); each item is exactly
  `{actor{id, login}, welcome, socialPoints, x}`, where the X link is
  present only when that link itself is public. Cursor-paginated,
  25 per page.
- `GET /api/v1/points/member?login=…` — one member in the same
  projection (`publicMember`: actor, joinedAt, public, welcome,
  socialPoints), or JSON `null`. A login shared by more than one
  public record fails closed to `null`: "Login collisions fail
  closed; numeric actor identity remains canonical."

The directory is a census, not a live query: `profiles.json` carries
a `generatedAt`, covers the collected repositories, and — per the
`ProfileIndex` doc comment in `src/lib/profiles.ts` — keeps the last
census of a repository that stops being collected, "so a removed
project does not erase contributor history". It also publishes an
issue-history section (`issues`) alongside `people`.

### 3. Wallet linking: public claim records, authenticated creation

A profile's wallet is a **wallet claim**: a standalone record binding
a numeric GitHub actor ID to a chain address
(`backend/trace/handler.ts`).

- **Reading is public.** `isPublicWalletRead` admits, with no
  session: `GET /api/v1/wallet-claims/actors/<numericId>/current`
  (the actor's current claim, or JSON `null` — "a valid actor without
  a claim is a successful read"), `GET /api/v1/wallet-claims/<claimId>`
  (one claim, served `cache-control: public, max-age=31536000,
  immutable`), and `GET /api/v1/wallet-claims/<address>/possession`
  (the published possession-attestation view). The current-claim read
  is served `cache-control: public, max-age=60, must-revalidate`.
  The profile page's browser fetch validates what it gets: the
  claim's `githubActorId` must equal the profile's numeric ID and
  the address must be a valid Solana funding address
  (`useCurrentWallet` in `src/ProfilePage.tsx`).
- **The public projection is fixed** (`publicWalletClaim`):
  `claimId`, `githubActorId`, `githubLogin`, `address`, `chain`,
  `source`, `issueRepository`, `issueNumber`, `sourceBodySha256`,
  `observedAt`, `recordDigest`, `supersedesClaimId`. A claim is
  therefore a citable public record: it names where the binding was
  observed (a registry write, `source: "d1_registry"`, or a public
  GitHub issue statement) and hashes what was observed.
- **Creating or replacing a claim is not public.** Creation requires
  an authenticated writer actor (`assertWriter`), and the claim is
  bound to the authenticated actor's own ID and login — the request
  body cannot name someone else. A replacement must name the current
  claim as `supersedesClaimId`; a mismatch is refused with 409
  `stale_wallet_claim`, so claims form a single supersession chain
  per actor and chain. Re-submitting the identical registry claim is
  idempotent. Each creation writes an audit record
  (`wallet_claim.created`) with the record digest.
- The cycle contributor records carry a wallet proof of the same
  shape family (`{address, chain, sourceUrl}`, validated in
  `src/lib/cycle-index.ts`), generated from the allocations that
  already bind the wallet to the actor; that is the record the
  profile page falls back to when no current claim resolves.

How a linked wallet is then used as payout consent is issue #3's
territory (covered by PR #32) and the vault owner's registration
check is issue #8's (PR #54); this packet covers only the identity
record and its display. Inbox mechanics are likewise left to the
open packet that documents them (PR #34).

### 4. Public versus server-only

Public, readable without a session (verified live, section below):

- The identity directory (`/data/profiles.json`), the leaderboard
  snapshot and the cycle index (`/data/…`), including penalty
  history and per-repository PR counts for every recorded
  contributor.
- Public members and their join dates, welcome and social points
  (`/api/v1/points/people`, `/api/v1/points/member`), for members
  flagged public.
- Any actor's current wallet claim and any single claim by ID, in
  the fixed projection above.

Server-side only (from the code; not observable in any public read):

- The session token itself (only its SHA-256 hash is stored), the
  full member row (e.g. `closed_at`, the stored node-ID actor key
  beyond its public projection), and non-public members: the public
  views filter them out entirely.
- The identity Worker's flow state (state and capability hashes, the
  encrypted PKCE verifier) and unconsumed assertions.
- Wallet-claim creation and its audit records; the claim store
  beyond the public projection.
- The points journal and balances themselves — issue #2's territory
  (PR #23); the profile page shows only the published aggregates.

## Verification

Checker added by this PR (standard library only):

```
python3 scripts/verify-identity-profile.py            # live checks
python3 scripts/verify-identity-profile.py --offline U_kgDOFFtd0A
python3 -m pytest tests/                              # offline tests
```

Observed on 2026-11-11, the live run printed `ALL CHECKS PASSED`:

- Directory: exactly one record for `dd12m54` (directory
  `generatedAt` 2026-11-07T12:40:42.649Z; 1,954 people, 17
  repositories). Its node ID `U_kgDOFFtd0A` decoded to `341532112`,
  matching the `u/341532112` in its own avatar URL — the same decode
  the checker's `--offline` mode performs, and the same value
  obtained by hand-encoding `[0, 341532112]` back to
  `U_kgDOFFtd0A`. The record's per-repository counts (9 repositories)
  total 483 merged / 209 open / 110 closed at that generation.
- Member view: `GET /api/v1/points/member?login=dd12m54` returned
  `{"actor":{"id":"U_kgDOFFtd0A","login":"dd12m54"},
  "joinedAt":"2026-10-12T14:40:38.498Z","public":true,"welcome":5,
  "socialPoints":10}` — the actor ID is the node ID, as the join code
  prescribes. `GET /api/v1/points/people` returned a full page of 25
  items, every item carrying exactly the four public fields. (Both
  reads go through the site's own origin; addressed to the API
  origin directly, the same paths answer `403 origin_forbidden`.)
- Wallet claim: `GET /api/v1/wallet-claims/actors/341532112/current`
  answered 200 without any credential, with
  `cache-control: public, max-age=60, must-revalidate` and exactly
  the 13 public projection fields: claim `8a16d98f-d587-4eb8-a2a3-
  b5bcb79c736f`, `githubActorId "341532112"`, `source "d1_registry"`,
  `observedAt 2026-10-12T15:02:43.351Z`, `supersedesClaimId null` —
  a first claim, still current.
- Snapshot: the manifest (`slop-leaderboard-parts-v1`) lists
  content-addressed parts; each part matched its published size and
  SHA-256, and the assembled 34,251,751 bytes matched the manifest
  digest. The assembled snapshot carries the `leaders`, `penalties`
  and `reviewExclusions` arrays the profile code consumes.
- Identity Worker: bare GETs to `https://identity.slop.cash/`,
  `/v1/oauth/start` and `/v1/oauth/poll` answered
  `404 {"error":"not_found"}` — no public read surface, as expected
  for a flow-only Worker.
- Tests: `tests/test_verify_identity_profile.py` adds 4 offline
  decoder tests (current form, legacy form, a non-canonical uint64
  spelling of a small ID rejected, garbage rejected); the existing
  selector tests still pass (8 passed in total, run by direct
  function execution where pytest is unavailable).

## Notes

- **Cycle history is code-verified, not live-verified.** Repeated
  reads of `/data/cycles/index.json` during this session returned
  the current generation (`generatedAt` 2026-11-10T11:02:16.110Z)
  with an empty `cycles` list, while one earlier read returned a
  stale generation listing 30 project entries. The per-cycle
  contributor mechanism (including the wallet-proof fallback) is
  therefore cited from the code and the published file layout only;
  no contributor-level cycle claim is made from live data.
- **Snapshot counts are generation-dependent.** Two digest-verified
  assemblies in this session returned different generations (in one,
  `leaders` held 989 records and `penalties` 26; in another,
  `generatedAt` 2026-11-07T12:34:27.456Z, `leaders` held 194 and
  `penalties` 0). This packet claims the schema and the consumption
  path, never a count.
- **No sign-in was performed.** The session and assertion flows are
  documented from the public code; exercising them would require the
  author's own GitHub OAuth, which a research packet does not need —
  the public surface is the claim, and it is fully readable without
  one.
- Adjacent boundaries: points rules and the journal are issue #2
  (PR #23); payout paths and wallet-as-consent are issue #3
  (PR #32); owner-vault registration verification is issue #8
  (PR #54); the inbox cursor is PR #34; payment-wallet registration
  lineage is PR #36. None of those are duplicated here.

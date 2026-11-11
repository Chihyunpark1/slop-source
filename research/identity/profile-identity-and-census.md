# Profile identity — keyed by GitHub actor id, validated as a census, resolved only on agreement (Issue #7)

## Target

The public contributor profile of the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #7 (Identity &
profiles): the profile census validator `src/lib/profiles.ts`
(`assertProfiles`, `issueHistoryReconciles`), the census publisher
`scripts/generate-profiles.ts`, the profile page
`src/ProfilePage.tsx` (`currentProfileActor`), the census loader
`src/Profiles.tsx` (`loadProfiles`), and the actor-id decoder
`src/lib/github-actor.ts` (`githubUserIdFromNodeId`). Live data: the
published census at `https://slop.cash/data/profiles.json`.

## Claim

A public profile is keyed by the contributor's stable GitHub actor
id, never by login. The census is a prebuilt file,
`/data/profiles.json`, that the browser validates strictly before
trusting — every login must match the GitHub login pattern, every
avatar must come from GitHub's avatar host over HTTPS, and the
per-person pull-request counts must reconcile exactly with the
per-repository totals. The profile page then resolves a typed login
to an actor only when the ledger, the membership record, and the
census all agree; any source can veto a stale login, so a renamed
login cannot take over another contributor's page, wallet, or
history.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch.

### 1. The identity key is the actor id; the login is only a label

A profile record carries three identity fields: `id`, `login`, and
`avatarUrl`. The `id` is the GitHub user node id (the `U_kgDO…`
string); the decoder in `src/lib/github-actor.ts` explains why that
matters: the id survives renames and deleted accounts, so records
can be joined by actor with no GitHub request. The decoder accepts
two forms — legacy ids (base64 of `04:User<id>`) and current ids
(`U_` plus base64url of the MessagePack array `[0, id]`) — and
rejects anything that is not the canonical spelling GitHub emits,
including stripped or added padding and non-zero unused trailing
bits, which a plain base64 decode would otherwise discard silently.
The avatar URL is derived from the numeric id, not the login:
`https://avatars.githubusercontent.com/u/<numeric id>`.

### 2. The census validator rejects anything that does not add up

`assertProfiles()` in `src/lib/profiles.ts` runs over the whole
published census before the browser uses it. The rules it enforces:

- The file is schema version `"1"` or `"2"`, with `startedAt` no
  later than `generatedAt`, and every collected repository present
  exactly once.
- Every person has a unique `id` matching a 4–256 character
  base64-ish pattern, a `login` matching the GitHub login pattern
  (starts alphanumeric, then letters, digits, or hyphens, at most
  39 characters), and an avatar URL that is HTTPS, on host
  `avatars.githubusercontent.com`, with no username, password, or
  port.
- Every per-repository row names a repository in the census
  inventory, appears once per person, and holds non-negative
  integer merged, open, and closed counts.
- The census reconciles exactly: for each repository, the sum of
  every person's merged, open, and closed counts plus that
  repository's `excluded` count must equal its published `count`.
  A repository outside the census keeps its last counts only when
  it is a registered or legacy repository, so removing a project
  does not erase contributor history.
- Schema version `"2"` adds an issue history, and a version `"1"`
  file must not carry one. Issue records must have unique ids,
  positive issue numbers, an author id that names a person in the
  census (or null), timestamps in order (created no later than
  observed, observed no later than the census generation), and an
  event list whose kinds are only closed, reopened, duplicate,
  unmarked-duplicate, or transferred, in non-decreasing time order.
  Replaying the visible close/reopen events must reproduce the
  record's current state and reason — `issueHistoryReconciles()` —
  and a record flagged as having incomplete history must actually
  fail to reconcile, while an unflagged record must reconcile.
  Records for paused projects are kept as `archived`: not
  displayed, but resumed if the project reactivates.

### 3. The census is published atomically; retired names are carried, not dropped

`scripts/generate-profiles.ts` collects pull requests per repository
through the GitHub GraphQL API (100 per page, oldest first),
validates the result with `assertProfiles()`, and publishes it to
`public/data/profiles.json` by writing a `.tmp` file and renaming
it into place. When a repository is renamed, its old and new names
resolve to the same canonical repository, so the previous census
row is replaced by the fresh collection instead of being added to
it; rows for retired projects, and rows the registry does not know,
are still carried forward.

### 4. The page resolves a login only when every source agrees

`src/Profiles.tsx` loads `/data/profiles.json` with `cache:
"no-cache"`, an 8 MiB size cap, and runs `assertProfiles()` on the
bytes before use. A comment in the loader states the intent: a new
mount stays loading so a reassigned GitHub login cannot use old
identity, and stored bytes are reused only after the server
revalidates the identity directory.

`currentProfileActor()` in `src/ProfilePage.tsx` matches the typed
login case-insensitively, then checks every identity source before
selecting an actor: the signed-in member, the ledger leaders, the
review-exclusion reviewers, and the census directory. The code
comment is explicit — every identity source can veto a stale login,
and the page waits for the session, membership, and directory
before selecting the actor for wallet and history reads. A
candidate is rejected if any source shows the same login on a
different actor id, or the same actor id under a different login.
The directory can resolve an inactive actor, but it cannot override
a known rename: if the directory yields anything other than exactly
one candidate, the page shows no actor at all. Until the ledger or
profile data names the login, the page links to no GitHub profile —
the path is only what the visitor typed — and an unknown login gets
an "unknown contributor" state with a link back to the contributor
search.

Once resolved, the page shows the contributor identity (avatar and
login, linking out to GitHub), the current payout wallet or the
most recent past wallet (shortened to first and last four
characters, linked to its source), points, per-project bars for the
current cycle, cycle history newest first, and a penalty history
section when penalties exist.

## Verification

Fetched the live census on 2026-11-11 (~21:06 KST):

- `curl https://slop.cash/data/profiles.json` → HTTP 200,
  4,959,596 bytes (under the 8 MiB client cap).
- `schemaVersion: "2"`, `startedAt: 2026-11-07T12:34:42.948Z`,
  `generatedAt: 2026-11-07T12:40:42.649Z`, 1,954 people, 17
  repositories, with an issue history present.
- WalkCrypto's record: id `U_kgDOFDm-uw`, login `WalkCrypto`,
  avatar `https://avatars.githubusercontent.com/u/339328699?v=4`.
  Decoding the node id (base64url of the MessagePack array
  `[0, id]`) gives numeric id 339328699, exactly the id in the
  avatar URL. Its per-repository counts include
  lalalune/hyperliquid-source with 668 merged, 18 open, 31 closed;
  lalalune/pumpfun-source with 138 merged, 0 open, 114 closed; and
  bruhosdotai/bruhOS with 0 merged, 10 open, 0 closed.
- Checked all 1,954 people: zero login-pattern violations and
  zero avatar-host violations.
- The census reconciles exactly: the sum of every person's merged,
  open, and closed counts is 42,495; the repositories' `excluded`
  counts sum to 1,157; together 43,652, equal to the sum of the
  repositories' published `count` values.
- The issue history reconciles too: 9,885 items plus 3 archived,
  `firstObservedAt: 2026-10-09T04:17:46.859Z`, zero records where
  the incomplete-history flag disagrees with the replay check, and
  the 9,884 available items equal the sum of the per-repository
  issue counts.

To re-check: fetch the URL above and repeat the sum and pattern
checks, or read `src/lib/profiles.ts` (`assertProfiles`,
`issueHistoryReconciles`), `src/ProfilePage.tsx`
(`currentProfileActor`), and `src/Profiles.tsx` (`loadProfiles`).

## Notes

- Not covered here: the points-membership join flow that decides
  who counts as a member; the payout-wallet registration lineage
  (a separate open slice); how the census collection authenticates
  to GitHub and pages through repositories; and the profile rename
  end-to-end test (`tests/e2e/profile-rename.spec.ts`).
- The census is a build artifact: it is only as fresh as the last
  `generate-profiles.ts` run (this snapshot is from 2026-11-07),
  and the profile page shows a "contributor records are
  unavailable" state with a retry button when the fetch or the
  validation fails.

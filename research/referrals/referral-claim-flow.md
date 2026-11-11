# Referral claim flow, step by step

## Target

The referral claim flow in the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT): the page `src/ReferralClaims.tsx`,
the shared claim logic in `src/lib/referral-claims.ts`, and the API in
`backend/referrals/` (`claims.ts`, `cache.ts`, `handler.ts`).
Issue #19 asks for the flow from invite to claim, what the user does
at each step, and what the system checks.

## Claim

A referral reward is claimed as a Merkle claim against the
ReferralDistributor contract on Robinhood Chain: the server files
accrual epochs and builds a claim only for the referrer's pinned
wallet, and the browser re-reads the live contract and refuses to ask
for a signature if the root or the amount has moved since the API
answered.

## Evidence

All file references are to `SlopDotCash/slopdotcash` at the
`development` branch.

1. **Accrual is filed server-side, per period.** The referral-accrual
   worker files records into `referral_accrual_files`; each record
   lists referrers by GitHub ID with a `cumulativeBase` amount and a
   Merkle leaf (with proof) per referrer
   (`backend/referrals/claims.ts` reads these records back;
   `workers/referral-accrual/` produces them). A snapshot of the
   distributor's on-chain state — current root, epochs, the
   `claimed` map, paused/ended flags — is cached in
   `referral_claim_cache` (`backend/referrals/cache.ts`).

2. **Nothing is shown before activation.** `GET /api/v1/referrals/me`
   requires a signed-in session (`401 sign_in_required` otherwise).
   It returns `{enabled: false}` when there is no claim cache row or
   when no accrual file has `mode='live'`. The code comment cites
   PRD section 11: only the owner's explicit activation files live
   accruals; dry runs do not (`backend/referrals/claims.ts`).

3. **The claim wallet is pinned.** The API reads the wallet from
   `referral_claim_wallets` for the signed-in GitHub ID. The page
   tells the user "Confirm a Robinhood wallet in Account — the first
   wallet included stays fixed" (`src/ReferralClaims.tsx`). Accrual
   is matched to the claim only when the filed record's entry has
   both the same GitHub ID and the same wallet.

4. **The API builds the claim.** For the active epoch
   (`activeClaimEpoch` in `backend/referrals/cache.ts`), the API
   finds the referrer's leaf in the filed record matching the cached
   root, and computes
   `claimable = cumulativeBase − claimed[wallet]`, where `claimed`
   is the distributor's on-chain cumulative counter from the
   snapshot. If `claimable > 0` it returns
   `claim = {period, epoch, root, cumulativeBase, proof}`.
   The remainder shows as pending: a newer, not-yet-active epoch is
   reported as `pendingUntil` (its `claimableAt`), and the totals
   must satisfy `claimed + claimable ≤ accrued`, or the API throws
   "Referral claim totals differ".

5. **Stale, paused, ended, and voided states block or defer.**
   The snapshot is `stale` when it is older than
   `REFERRAL_CACHE_MAX_AGE_MS` (48 hours, `src/lib/referral-claims.ts`)
   or carries an error, and the page then offers only a refresh.
   `paused` and `ended` come from the snapshot; a voided latest epoch
   is surfaced as `latestVoided` and earns no pending notice.

6. **The browser re-verifies before any signature.**
   `reviewReferralClaim` (`src/lib/referral-claims.ts`) requires the
   status to be `ready`, requires the connected wallet's address to
   equal the pinned wallet, then re-reads the contract live:
   `currentRoot()` must still match the claim's root and epoch, and
   `claimed(wallet)` must still make
   `cumulativeBase − claimed` equal the displayed claimable amount.
   Any mismatch aborts with "The claim root changed" or "The claim
   amount changed" — the wallet is never asked to sign stale data.

7. **The user signs one contract call.** `sendReferralClaim` calls
   `claim(uint256 cumulative, bytes32[] proof)` on the distributor
   (ABI in `src/lib/referral-claims.ts`) from the user's wallet.
   Before sending, the page stores a marker in browser storage
   (`slop:referral-claim:<network>:<distributor>:<wallet>`); if the
   send result is unknown, it tells the user to check wallet
   activity before another attempt, so a claim is not sent twice.

8. **After the claim.** Because the contract's `claimed(address)`
   counter is cumulative, a later epoch only pays the difference
   between the new cumulative amount and what was already claimed.
   The page waits for the verified record (the cache) to refresh
   before showing new totals (`src/ReferralClaims.tsx`).

## Verification

- Read the API path end to end: `backend/referrals/handler.ts`
  routes `/api/v1/referrals/me` to `handleReferralClaims` in
  `backend/referrals/claims.ts`; every numbered step above names the
  function or query that performs it.
- Check the claim math in `backend/referrals/claims.ts`:
  `claimable = cumulative − claimed`, the filed record is re-read
  for the exact `(period, root, totalBase)` of the cached epoch,
  and the totals assertion throws when they disagree.
- Check the pre-sign guards in `src/lib/referral-claims.ts`
  (`reviewReferralClaim`): wallet equality, live `currentRoot()`,
  live `claimed()`, and the ABI, which contains exactly one
  state-changing function, `claim(uint256,bytes32[])`.
- The backend behaviour is covered by `backend/referrals/claims.test.ts`
  in the same repository.

## Notes

- **Program state.** Per the PRD text quoted in the claims code and
  the PRD's referral section, the program is not announced before the
  owner's explicit activation, and accrual stays `off` or `dry_run`
  until then. This packet documents the implemented flow; it does
  not claim the program is live.
- **Invite attribution** (how a signup is credited to a referrer)
  happens before step 1, inside the accrual worker; this packet
  covers the claim flow named in Issue #19 and does not document the
  attribution rules.
- Amounts are token base units (18 decimals) carried as strings and
  compared as `BigInt` throughout the claim path.

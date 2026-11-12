# The 13 Slop Cash Background Workers

## Target

The background workers of the public Slop Cash codebase (`SlopDotCash/slopdotcash`, MIT licensed, commit `1b0a4d8ff1d62efe781ddd69be774531909f8ff2`) located in `workers/`. This addresses Issue #18 in area 13 ("Workers") of `research/scope.md`.

## Claim

The Slop Cash platform architecture operates exactly 13 specialized background workers across payment settlement, identity, notifications, security vetting, and contribution review.

## Evidence

Public source code in `SlopDotCash/slopdotcash` at `workers/` defines the following 13 workers, each configured with dedicated entrypoints, environments, and execution triggers:

1. **`fee-converter` (`workers/fee-converter/`)**
   - **Description**: Converts project tokens collected by network fee wallets into that network's native Circle USDC (on both EVM and Solana), applying the 2% protocol fee.
   - **Trigger**: Periodic cron schedule / keeper execution processing accumulated fee balances.
   - **Source**: `workers/fee-converter/README.md`, `workers/fee-converter/core.ts`

2. **`identity` (`workers/identity/`)**
   - **Description**: Handles GitHub OAuth sign-in using the authorization-code flow with PKCE, issuing a single-use 90-second identity assertion to authenticate contributors without storing long-lived personal access tokens or credentials.
   - **Trigger**: HTTP requests from clients initiating or completing GitHub OAuth login flows.
   - **Source**: `workers/identity/README.md`, `workers/identity/handler.ts`

3. **`notify` (`workers/notify/`)**
   - **Description**: Sends private transactional email notifications for Slop inbox messages, admin project application alerts, and internal Slopbot operational/cost notices using Cloudflare Email bindings.
   - **Trigger**: Cloudflare Queue messages and internal service binding calls triggered by notification events.
   - **Source**: `workers/notify/README.md`, `workers/notify/handler.ts`

4. **`operator-keeper` (`workers/operator-keeper/`)**
   - **Description**: An operator-owned Cloudflare worker that monitors public Slop on-chain state and invokes permissionless contract execution functions using the operator's dedicated gas wallet and RPC limits.
   - **Trigger**: Scheduled cron intervals configured on the operator's Cloudflare account.
   - **Source**: `workers/operator-keeper/README.md`, `workers/operator-keeper/index.ts`

5. **`payment-executor` (`workers/payment-executor/`)**
   - **Description**: Signs and broadcasts on-chain reward distributions for approved obligations and verified wallet claims across EVM and Solana networks.
   - **Trigger**: Scheduled release workflows and private service binding calls from the payments dispatcher.
   - **Source**: `workers/payment-executor/README.md`, `workers/payment-executor/entrypoint.ts`

6. **`payments` (`workers/payments/`)**
   - **Description**: The core payment dispatcher and ledger scanner that tracks on-chain activity, reconciles monthly reward pool commitments, and manages order dispatch sequences.
   - **Trigger**: Scheduled workflow dispatches (`dispatch-clock.workflow.mjs`, `monthly-order.workflow.mjs`).
   - **Source**: `workers/payments/index.ts`, `workers/payments/reconcile.ts`

7. **`referral-accrual` (`workers/referral-accrual/`)**
   - **Description**: Calculates referral rewards from transaction volume and generates Merkle roots for on-chain claim verification (deferred with `REFERRAL_ACCRUAL_MODE="off"` at initial platform launch).
   - **Trigger**: Scheduled batch log processors scanning historical chain events.
   - **Source**: `workers/referral-accrual/README.md`, `workers/referral-accrual/core.ts`

8. **`security-payments` (`workers/security-payments/`)**
   - **Description**: Manages payouts for private security bounty findings using an isolated ledger and confidential notifications, keeping security payouts separate from public reward tables.
   - **Trigger**: Private administrative approval of validated vulnerability disclosures.
   - **Source**: `workers/security-payments/index.ts`

9. **`slopbot` (`workers/slopbot/`)**
   - **Description**: The hosted GitHub App worker implementing the `slopbot-v2` protocol; processes webhook events to triage PRs, estimate contribution sizes, award accepted-work Points, and enforce closure/penalty rules.
   - **Trigger**: GitHub webhook events (`pull_request`, `pull_request_review`, `issue_comment`).
   - **Source**: `workers/slopbot/README.md`, `workers/slopbot/entrypoint.ts`

10. **`vetting` (`workers/vetting/`)**
    - **Description**: Static security analyzer that scans submitted repositories and skill bundles for malicious patterns (wallet drainers, credential stealers, prompt injection, and unauthorized network exfiltration) prior to project admission.
    - **Trigger**: Ingestion queue messages upon project registration or skill revision publication.
    - **Source**: `workers/vetting/README.md`, `workers/vetting/service.ts`

11. **`vetting-backup` (`workers/vetting-backup/`)**
    - **Description**: Archives daily raw-byte snapshots of scanner evidence and qualification artifacts into cold storage for reproducible provenance audits.
    - **Trigger**: Scheduled daily cron workflow (`qualification-workflow.mjs`).
    - **Source**: `workers/vetting-backup/README.md`

12. **`vetting-flags` (`workers/vetting-flags/`)**
    - **Description**: Staging qualification service that simulates and tests the two-flag automated project pause mechanism using fixture repositories.
    - **Trigger**: Automated staging qualification runs (`run-workflow.mjs`).
    - **Source**: `workers/vetting-flags/README.md`

13. **`vetting-sandbox` (`workers/vetting-sandbox/`)**
    - **Description**: Ephemeral Cloudflare sandbox runner that executes untrusted installation hooks and scripts within an isolated container to inspect runtime behavior.
    - **Trigger**: Internal service binding invocations from the `vetting` worker.
    - **Source**: `workers/vetting-sandbox/README.md`, `workers/vetting-sandbox/index.ts`

## Verification

To verify this inventory independently:

1. List the directories in `workers/` of `SlopDotCash/slopdotcash` at the pinned commit:
   ```bash
   gh api 'repos/SlopDotCash/slopdotcash/contents/workers?ref=1b0a4d8ff1d62efe781ddd69be774531909f8ff2' --jq '.[].name'
   ```
   Observed output:
   ```text
   fee-converter
   identity
   notify
   operator-keeper
   payment-executor
   payments
   referral-accrual
   security-payments
   slopbot
   vetting-backup
   vetting-flags
   vetting-sandbox
   vetting
   ```
   Output confirms exactly the 13 worker names listed above.
2. Verify the documentation and entrypoint for each worker in the canonical source tree at `https://github.com/SlopDotCash/slopdotcash/tree/1b0a4d8ff1d62efe781ddd69be774531909f8ff2/workers/<worker-name>`.

## Notes

- This packet satisfies the requirements of Issue #18 on `Chihyunpark1/slop-source`.
- Architectural relationships: `vetting-sandbox` and `vetting-backup` support the primary `vetting` engine; `security-payments` mirrors `payments` logic with a separate private database; `fee-converter` feeds into the USDC reward vaults handled by `payment-executor`.

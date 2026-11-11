# Inventory the 13 worker components

Refs #18

## Target

The 13 components named in issue #18 under the upstream workers directory at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The 13 components cover scheduled jobs, request and queue handlers, and workflow-driven qualification code.

## Evidence

| Component | Role and trigger |
| --- | --- |
| fee-converter | Runs fee-conversion work on its scheduled handler. Its config declares a one-minute cron. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/fee-converter/index.ts#L190-L209) · [Config](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/fee-converter/wrangler.toml#L4-L15) |
| identity | Serves wallet identity flows over HTTP and runs scheduled maintenance. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/identity/index.ts#L469-L485) · [Config](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/identity/wrangler.toml#L34-L38) |
| notify | Delivers inbox-related emails, internal cost notices and legacy project-application notices. The request handler accepts delivery work. A scheduled handler exists, while the checked-in cron list is empty. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/notify/index.ts#L125-L160) · [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/notify/README.md) · [Config](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/notify/wrangler.toml#L25-L28) |
| operator-keeper | Wraps the payment keeper for an operator's own account. The template provides a scheduled entry point with an empty cron list. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/operator-keeper/index.ts#L108-L140) · [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/operator-keeper/README.md) |
| payment-executor | Executes approved payout work in restricted test roles, with HTTP handlers and a scheduled recovery path. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/payment-executor/index.ts#L861-L910) · [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/payment-executor/README.md) |
| payments | Runs scheduled dispatch and recovery for payment obligations. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/payments/index.ts#L695-L760) |
| referral-accrual | Processes referral accrual and settlement work through a scheduled handler when enabled. The repository records a launch deferral. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/index.ts#L80-L113) · [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/README.md) |
| security-payments | Uses the payment dispatcher on a separate security-bounty ledger. Its scheduled entry point makes reserved obligations eligible after wallet authorization. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/security-payments/index.ts#L1-L32) |
| slopbot | Accepts GitHub-facing requests, processes queued jobs and runs scheduled background work. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/slopbot/index.ts#L236-L253) · [Scheduled and queue handlers](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/slopbot/index.ts#L522-L570) |
| vetting | Scans project revisions for admission or explicit investigation. The directory documents the scanner pipeline. [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting/README.md) |
| vetting-backup | Starts a daily scanner-evidence backup at 02:17 UTC and processes object-copy work through a queue. [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting-backup/README.md) · [Config](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting-backup/wrangler.toml#L1-L25) |
| vetting-flags | Provides qualification fixtures for the two-flag pause flow. It is invoked through the flags scope of the vetting recovery workflow. [Overview](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting-flags/README.md) · [Workflow code](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting-flags/workflow.ts) |
| vetting-sandbox | Handles scanner execution requests through the sandbox runner binding. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting-sandbox/index.ts#L1-L65) · [Config](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/vetting-sandbox/wrangler.toml#L1-L22) |

## Verification

At the pinned commit, compare the issue's 13 names to the directories under workers. Check each handler or workflow and compare cron claims against the corresponding configuration. Verified by static source inspection. Deployment and runtime scheduling were outside this check.

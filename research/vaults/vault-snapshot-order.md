# Document vault snapshot refresh ordering

Refs #8

## Target

Upstream vaults behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/vault-snapshots.ts#L65-L163) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

Vault snapshot refreshes prioritize block height and use observation time to order refreshes of the same block.

## Evidence

The stored row is identified by project, network and vault. The writer checks that the observation matches the reviewed deployment and rejects a change to the asset or its decimals. A lower block height is classified as older. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/vault-snapshots.ts#L65-L163)

The upsert repeats ordering and cumulative-counter checks at write time. A later observation of the same block may update the row, while a lower block cannot displace a higher one even if observed later. Cumulative amounts are compared as canonical decimal strings so the comparison retains precision above SQLite int64. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/vault-snapshots.test.ts#L125-L265)

## Verification

Read the two ordering fixtures and compare their final stored height and observation timestamp with the write predicate. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.

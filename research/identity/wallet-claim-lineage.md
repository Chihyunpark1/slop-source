# Document payment wallet registration lineage

Refs #7

## Target

Upstream identity behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/wallet-registration.ts#L7-L76) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

Payment wallet registration tracks a claim chain by immutable GitHub actor ID and wallet chain, reusing an unchanged registry claim.

## Evidence

The lookup selects the claim with no successor for the actor and chain. An existing registry tip for the same address returns its existing ID, which lets a GitHub login rename preserve the claim. An earlier non-registry claim for the same address instead receives a registry successor. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/wallet-registration.ts#L7-L76)

New records reference the preceding claim. If a concurrent registration wins, the function rereads the tip and returns that ID. It signals a conflict if the winning address differs. This packet covers registry claims and leaves signing and authorization to their own flow. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/wallet-replacement.test.ts#L198-L229)

## Verification

Compare the query parameters and unchanged-address branch with the GitHub rename test. The test registers an address, changes the login on the same actor and checks that the claim is reused. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.

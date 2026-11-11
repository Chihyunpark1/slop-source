# Document asset handling in public received totals

Refs #3

## Target

Upstream payouts behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/public-records.ts#L316-L362) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

Public received totals combine direct USD-micro amounts and qualifying vault net amounts, while grouping other assets separately by network and address.

## Evidence

The aggregation groups records by GitHub user ID. Direct transfers add their recorded micro-unit amounts. Finalized vault payments contribute their net amount to the USD total and project subtotal only if the network, asset address and decimals qualify under the USD asset predicate. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/public-records.ts#L316-L362)

Other vault assets accumulate as net base units in a separate network-and-address bucket. A synthetic contributor with 400 direct micro-units, 90 qualifying vault micro-units and 700 base units of a different asset has usdMicro of 490 and a separate otherAssets entry for 700 base units. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/public-records.ts#L363-L413)

## Verification

Traced the three inputs through the aggregation branches and checked the example arithmetic. The packet describes how records are aggregated and makes no claim about current payout amounts. Full upstream test suites and live services were outside the verification.

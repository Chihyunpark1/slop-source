# Document direct payout history pagination

Refs #3

## Target

Upstream payouts behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/direct-history.ts#L8-L56) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

Direct transfer history fixes an append boundary on the first page and carries it through subsequent pages.

## Evidence

The reader captures the highest stored row ID when no boundary is supplied. It returns matching project or actor rows with IDs above the cursor and at or below the boundary in ascending order. It queries up to 101 rows, returns up to 100 and uses the last returned row ID as the next cursor when more exist. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/direct-history.ts#L8-L56)

The total count covers matching rows through the boundary. The reported micro-unit sum covers the rows returned on that page. Rows appended beyond the original boundary appear only in a new traversal with a fresh boundary. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/payments/direct-history.workflow.mjs#L100-L167)

## Verification

Read the fixture that appends rows after page one and compare each continuation's through value with the first response. Compare the COUNT query and the sum over selected transfers. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.

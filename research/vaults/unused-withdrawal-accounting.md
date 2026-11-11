# Document unused EVM vault withdrawal accounting

Refs #8

## Target

Upstream vaults behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/evm/src/ProjectEscrow.sol#L779-L800) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

An owner withdrawal consumes free balance by the gross amount and transfers the net amount after a fee rounded up in base units.

## Evidence

The entry point rejects zero and gross amounts above freeBalance. It subtracts gross from free balance, adds gross to the cumulative withdrawal counter, and increments both withdrawal-fee totals and accrued fees. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/evm/src/ProjectEscrow.sol#L779-L800)

The fee helper charges the ceiling of gross divided by 50. For a gross withdrawal of 860 base units, the fee is 18 and the owner receives 842. The contract emits gross, net and fee, while fee claiming has its own entry point. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/evm/test/FableEscrow.t.sol#L290-L305)

## Verification

Compared the state updates with the upstream 860-unit fixture and the fee helpers at lines 432–442 of ProjectEscrow.sol. Independently checked the integer arithmetic. Full upstream test suites and live services were outside the verification.

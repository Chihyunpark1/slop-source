# Document chain-aware wallet address comparison

Refs #7

## Target

identity behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/wallets.ts#L47-L66)

## Claim

The comparison helper treats EVM addresses as case-insensitive and Solana public-key strings as case-sensitive.

## Evidence

The EVM branch lowercases both arguments. The Solana branch compares the original strings directly. Validation is exposed separately through isWalletAddress and is not performed by the equality helper. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/wallets.ts#L47-L66)

## Verification

Compare the same pair of strings differing only in case with each family. Expect equality for the EVM branch and inequality for Solana. The author checked the source statically. The example is a reviewer check.

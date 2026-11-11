# Selector 9dc29fac is burn(address,uint256)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `9dc29fac` in the SLOP token dispatcher is
`burn(address,uint256)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("burn(address,uint256)")` are `9dc29fac`:

   ```text
   keccak256("burn(address,uint256)")
     = 9dc29fac0ba6d4fc521c69c2b0c636d612e3343bc39ed934429b8876b0d12cba
   selector = 0x9dc29fac
   ```

2. **The selector is in the deployed bytecode.** `9dc29fac` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 182,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 806395d89b41146102eb5780639dc29fac14610200578063a9059cbb146101cf57 ...
                                  ^^^^^^^^^^
                                  PUSH4 9dc29fac, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, exactly as it does for the other
   known selectors (for example `63a9059cbb` = `transfer(address,uint256)`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("burn(address,uint256)")` and take the first 4 bytes.
   Expected: `9dc29fac`.
2. Search the deployed bytecode for `9dc29fac`:
   `grep -o 9dc29fac research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `burn` is a state-changing function, so it cannot be called with
  `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call `burn`
  or what it does when called.
- This packet covers one selector only. The other 17 functions in
  Issue #15 are not covered here.

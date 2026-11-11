# Selector a9059cbb is transfer(address,uint256)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `a9059cbb` in the SLOP token dispatcher is
`transfer(address,uint256)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("transfer(address,uint256)")` are `a9059cbb`:

   ```text
   keccak256("transfer(address,uint256)")
     = a9059cbb2ab09eb219583f4a59a5d0623ade346d962bcd4e46b11da047c9049b
   selector = 0xa9059cbb
   ```

2. **The selector is in the deployed bytecode.** `a9059cbb` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 193,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 6395d89b41146102eb5780639dc29fac14610200578063a9059cbb146101cf578063dd62ed3e1461 ...
                                                     ^^^^^^^^^^
                                                     PUSH4 a9059cbb, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `burn` selector
   (`63 9dc29fac`) and before another selector (`63 dd62ed3e`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("transfer(address,uint256)")` and take the first 4 bytes.
   Expected: `a9059cbb`.
2. Search the deployed bytecode for `a9059cbb`:
   `grep -o a9059cbb research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `transfer` is a state-changing function, so it cannot be called with
  `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call
  `transfer` or what it does when called.
- This packet covers one selector only. The other 16 functions are not
  covered here. `burn` (`9dc29fac`) was verified in a previous packet.

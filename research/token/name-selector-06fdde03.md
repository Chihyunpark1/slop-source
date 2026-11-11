# Selector 06fdde03 is name()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `06fdde03` in the SLOP token dispatcher is
`name()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("name()")` are `06fdde03`:

   ```text
   keccak256("name()")
     = 06fdde0383f15d582d1a74511486c9ddf862a882fb7904b3d9fe9b8b8e58a796
   selector = 0x06fdde03
   ```

2. **The selector is in the deployed bytecode.** `06fdde03` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 39,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 5f3560e01c90816301ffc9a7146108e65750806306fdde0314610814578063095ea7b31461079257806318160ddd14610775 ...
                                             ^^^^^^^^^^
                                             PUSH4 06fdde03, EQ
   ```

   The neighbouring entries are the same dispatcher comparisons for
   `095ea7b3` (`approve(address,uint256)`) and `18160ddd`
   (`totalSupply()`), so this entry is one of the contract's public
   function routes, not data.

3. **The function answers on the live contract.** At block
   111,671,819 (2026-11-11), an `eth_call` to the contract with call
   data `0x06fdde03` returned an ABI-encoded string:

   ```text
   0x0000000000000000000000000000000000000000000000000000000000000020
     0000000000000000000000000000000000000000000000000000000000000009
     536c6f7020436173680000000000000000000000000000000000000000000000
   ```

   Offset `0x20`, length 9, bytes `536c6f702043617368` = `"Slop Cash"`,
   which matches the token name recorded for this contract in
   `research/scope.md`. At the same block, `totalSupply()`
   (selector `0x18160ddd`) returned `100,000,000 * 10^18`, confirming
   the contract is the live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector with the repository's checker:
   `python3 scripts/verify-selector.py "name()" --bytecode research/slop-bytecode.hex`
   — expect selector `0x06fdde03`, found at byte offset 39 in the
   dispatcher pattern.
2. Search the deployed bytecode for `06fdde03`:
   `grep -o 06fdde03 research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Call the live contract at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` with data `0x06fdde03` returns the ABI encoding of
   `"Slop Cash"`.

## Notes

- `name()` is a read-only function, so the live `eth_call` above
  observes its actual return value, not only its route in the
  dispatcher.
- This packet covers one selector only. The other functions listed
  in Issue #15 are not covered here.

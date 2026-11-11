# Selector dd62ed3e is allowance(address,address)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `dd62ed3e` in the SLOP token dispatcher is
`allowance(address,address)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("allowance(address,address)")` are `dd62ed3e`:

   ```text
   keccak256("allowance(address,address)")
     = dd62ed3e90e97b3d417db9c0c7522647811bafca5afc6694f143588d255fdfb4
   selector = 0xdd62ed3e
   ```

2. **The selector is in the deployed bytecode.** `dd62ed3e` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 204,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 9dc29fac14610200578063a9059cbb146101cf578063dd62ed3e1461017f5763f2fde38b146100e2575f80fd5b3461017b57602036 ...
                                                   ^^^^^^^^^^
                                                   PUSH4 dd62ed3e, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `transfer`
   selector (`63 a9059cbb`) and before the `f2fde38b` selector
   (`63 f2fde38b`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("allowance(address,address)")` and take the
   first 4 bytes. Expected: `dd62ed3e`.
2. Search the deployed bytecode for `dd62ed3e`:
   `grep -o dd62ed3e research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'allowance(address,address)'`
   — expect "found at byte offset 204".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `allowance` is a view function, so it can be observed via `eth_call`
  in principle. This packet identifies the selector only; it does not
  claim anything about what `allowance` returns for any given
  owner/spender pair.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.

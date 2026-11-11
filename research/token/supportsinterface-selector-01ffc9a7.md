# Selector 01ffc9a7 is supportsInterface(bytes4)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `01ffc9a7` in the SLOP token dispatcher is
`supportsInterface(bytes4)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("supportsInterface(bytes4)")` are `01ffc9a7`:

   ```text
   keccak256("supportsInterface(bytes4)")
     = 01ffc9a7a5cef8baa21ed3c5c0d7e23accb804b619e9333b597f47a0d84076e2
   selector = 0x01ffc9a7
   ```

2. **The selector is in the deployed bytecode — twice.** `01ffc9a7`
   appears exactly twice in `research/slop-bytecode.hex`, and the two
   occurrences are different things:

   (a) **Dispatcher entry, byte offset 27.** The `PUSH4` (`0x63`) +
   selector + `EQ` (`0x14`) pattern, followed by a jump — this is the
   dispatcher routing calls to this function:

   ```text
   ... 15610012575f80fd5b5f3560e01c90816301ffc9a7146108e65750806306fdde0314610814578063095ea7b31461079257806318160ddd1461077557 ...
                                         ^^^^^^^^^^
                                         PUSH4 01ffc9a7, EQ
   ```

   (b) **Function-body constant, byte offset 2346.** The same four
   bytes appear again as a `PUSH4` constant, but followed by `PUSH1`
   `0xe0` + `SHL` + `EQ` — not a dispatcher comparison. This is the
   `supportsInterface` implementation itself, loading the ERC-165
   interface ID constant `0x01ffc9a7` to compare it against the
   interface ID the caller asked about:

   ```text
   ... 60e11b8114908115610928575b5015158152f35b6301ffc9a760e01b14905083610921565b602060409281835280519182918282860152018484015e ...
                                                 ^^^^^^^^^^
                                                 PUSH4 01ffc9a7, PUSH1 0xe0, SHL, EQ
   ```

   The second occurrence corroborates the identification: the function
   body references the very interface ID its own selector stands for.

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("supportsInterface(bytes4)")` and take the first 4
   bytes. Expected: `01ffc9a7`.
2. Search the deployed bytecode for `01ffc9a7`:
   `grep -o 01ffc9a7 research/slop-bytecode.hex` — expect exactly two
   matches. The first (byte offset 27) is preceded by `63` (PUSH4)
   and followed by `14` (EQ): the dispatcher entry. The second (byte
   offset 2346) is preceded by `63` and followed by `60` (PUSH1):
   a constant in the function body, not a dispatcher entry.
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'supportsInterface(bytes4)'` — it
   reports both occurrences.
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- This packet identifies the selector only. It does not claim a
  specific return value for any interface ID; the behavior of
  `supportsInterface` for a given input was not tested here.
- This packet covers one selector only. The other 15 functions are not
  covered here. `burn` (`9dc29fac`) and `transfer` (`a9059cbb`) were
  verified in previous packets.

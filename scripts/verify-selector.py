#!/usr/bin/env python3
"""Verify a function selector against deployed EVM bytecode.

Computes the selector (first 4 bytes of keccak256 of the function
signature) and checks whether it appears in a deployed bytecode file,
and whether it sits in the dispatcher pattern (PUSH4 + selector + EQ).

Pure Python standard library only. No dependencies.

Usage:
    python3 scripts/verify-selector.py "burn(address,uint256)"
    python3 scripts/verify-selector.py "burn(address,uint256)" --bytecode research/slop-bytecode.hex
    python3 scripts/verify-selector.py "transfer(address,uint256)" --bytecode research/slop-bytecode.hex
"""

import argparse
import re
import sys

# --- Keccak-f[1600] (Keccak-256, as used by Ethereum) ---

_MASK64 = 0xFFFFFFFFFFFFFFFF

_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

_R = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def _rol(x, n):
    return ((x << n) | (x >> (64 - n))) & _MASK64


def _keccak_f(state):
    # state: 25 64-bit words, index = x + 5*y
    for rnd in range(24):
        # Theta
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
             for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= d[x]
        # Rho and Pi
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(state[x + 5 * y], _R[x][y])
        # Chi
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = (
                    b[x + 5 * y]
                    ^ ((~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y])
                ) & _MASK64
        # Iota
        state[0] ^= _RC[rnd]
    return state


def keccak256(data: bytes) -> bytes:
    """Keccak-256 digest (pre-NIST Keccak, as used by Ethereum)."""
    rate = 136  # bytes
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != rate - 1:
        padded.append(0x00)
    padded.append(0x80)
    state = [0] * 25
    for off in range(0, len(padded), rate):
        block = padded[off:off + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[i * 8:(i + 1) * 8], "little")
        state = _keccak_f(state)
    out = b""
    for i in range(4):
        out += state[i].to_bytes(8, "little")
    return out


def selector_of(signature: str) -> str:
    """First 4 bytes of keccak256(signature), as a hex string."""
    return keccak256(signature.encode("utf-8")).hex()[:8]


def find_selector(bytecode_hex: str, selector: str):
    """Find a selector in bytecode hex. Returns a list of byte offsets
    where it appears in the dispatcher pattern (PUSH4 + selector + EQ).
    """
    hits = []
    for m in re.finditer(selector, bytecode_hex):
        byte_off = m.start() // 2
        before = bytecode_hex[m.start() - 2:m.start()]
        after = bytecode_hex[m.end():m.end() + 2]
        in_dispatcher = before == "63" and after == "14"
        hits.append((byte_off, in_dispatcher))
    return hits


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify a function selector against deployed EVM bytecode."
    )
    parser.add_argument("signature", help='Function signature, e.g. "burn(address,uint256)"')
    parser.add_argument(
        "--bytecode",
        help="Path to a deployed bytecode hex file (e.g. research/slop-bytecode.hex)",
    )
    args = parser.parse_args(argv)

    signature = args.signature.strip()
    sel = selector_of(signature)
    print(f'signature: {signature}')
    print(f'keccak256: {keccak256(signature.encode("utf-8")).hex()}')
    print(f'selector:  0x{sel}')

    if not args.bytecode:
        return 0

    try:
        bytecode_hex = open(args.bytecode, encoding="utf-8").read().strip()
    except OSError as e:
        print(f"error: cannot read {args.bytecode}: {e}", file=sys.stderr)
        return 2
    bytecode_hex = re.sub(r"^0x", "", bytecode_hex).strip()
    if len(bytecode_hex) % 2 != 0:
        print("error: bytecode hex has an odd length", file=sys.stderr)
        return 2

    hits = find_selector(bytecode_hex, sel)
    print(f"bytecode:  {args.bytecode} ({len(bytecode_hex) // 2} bytes)")
    if not hits:
        print(f"result:    selector 0x{sel} NOT FOUND in bytecode")
        return 1
    for byte_off, in_dispatcher in hits:
        pattern = "PUSH4 + selector + EQ (dispatcher)" if in_dispatcher else "raw match (not in dispatcher pattern)"
        print(f"result:    found at byte offset {byte_off} — {pattern}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

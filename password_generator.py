#!/usr/bin/env python3
"""
Password generator — create random passwords that satisfy Active Directory
default complexity (3 of 4 character classes) or a stricter all-4-classes
policy.

Stdlib only (argparse, secrets, string). Uses the secrets module, not
random, because these are credentials — secrets is cryptographically
strong.

Usage:
    python password_generator.py                  # 1 password, 16 chars
    python password_generator.py -n 5 -l 14       # 5 passwords, 14 chars
    python password_generator.py --no-symbols     # letters + digits only
    python password_generator.py --require-all    # force all 4 classes

Pairs with Reset-HDPassword.ps1 in the powershell-helpdesk-toolkit repo:
generate here, paste into the reset workflow over a secure channel.
"""

import argparse
import secrets
import string
import sys

# Ambiguous characters removed: 0/O, 1/l/I — fewer "is that a zero?" tickets
UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
LOWER = "abcdefghijkmnopqrstuvwxyz"
DIGITS = "23456789"
SYMBOLS = "!@#$%^&*-_=+"


def generate(length: int, use_symbols: bool, require_all: bool) -> str:
    pools = [UPPER, LOWER, DIGITS]
    if use_symbols:
        pools.append(SYMBOLS)

    if length < len(pools):
        raise ValueError(
            f"Length {length} is too short to include "
            f"{len(pools)} character classes."
        )

    # Guarantee at least one char from each required class, then fill
    # the rest from the combined pool, then shuffle. Without the shuffle,
    # the first characters would always be Upper/lower/digit/symbol in
    # order — a predictable pattern.
    required = [secrets.choice(p) for p in pools]
    if not require_all and not use_symbols:
        # AD default policy needs 3 of 4 classes; letters+digits gives
        # exactly 3 (upper, lower, digit). Keep all three guaranteed.
        pass
    alphabet = "".join(pools)
    remaining = [secrets.choice(alphabet) for _ in range(length - len(required))]
    chars = required + remaining
    # Fisher-Yates shuffle with secrets for the index selection
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate cryptographically random passwords."
    )
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="How many passwords to generate (default: 1)")
    parser.add_argument("-l", "--length", type=int, default=16,
                        help="Password length (default: 16)")
    parser.add_argument("--no-symbols", action="store_true",
                        help="Letters and digits only (still meets AD 3-of-4 rule)")
    parser.add_argument("--require-all", action="store_true",
                        help="Force all 4 character classes "
                             "(upper, lower, digit, symbol)")
    args = parser.parse_args()

    if args.length < 8:
        print("Warning: under 8 characters is weak — consider 14+.",
              file=sys.stderr)
    if args.count < 1 or args.count > 100:
        print("Error: count must be 1-100.", file=sys.stderr)
        return 2

    use_symbols = not args.no_symbols
    if args.require_all and not use_symbols:
        print("Error: --require-all needs symbols; drop --no-symbols.",
              file=sys.stderr)
        return 2

    try:
        for _ in range(args.count):
            print(generate(args.length, use_symbols, args.require_all))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

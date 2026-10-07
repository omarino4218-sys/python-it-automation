#!/usr/bin/env python3
"""
Log parser — scan a log file, count errors and warnings by type, and print
the top offenders.

Stdlib only (argparse, re, collections). Built for the classic helpdesk
workflow: a user says "the app keeps crashing," you pull the log, and in
one command you know exactly which error is spamming.

Usage:
    python log_parser.py app.log
    python log_parser.py app.log --top 10 --level ERROR
    python log_parser.py /var/log/syslog --pattern "Failed password"

Log lines are expected to look something like:
    2026-10-06 14:22:31 ERROR [auth] Failed login for user jdoe from 10.0.0.8
    2026-10-06 14:22:33 WARNING [disk] /var is 91% full
The parser is tolerant: lines without a recognizable level are counted
as UNKNOWN rather than crashing the run.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# Matches: timestamp, LEVEL, optional [tag], then the message.
# Example: "2026-10-06 14:22:31 ERROR [auth] Failed login for user jdoe"
LOG_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})?\s*"
    r"(?P<level>ERROR|WARN(?:ING)?|INFO|DEBUG|CRITICAL|FATAL)"
    r"\s*(?:\[(?P<tag>[^\]]+)\])?\s*"
    r"(?P<msg>.*)$",
    re.IGNORECASE,
)

# Normalize messages so "Failed login for user jdoe" and
# "Failed login for user asmith" count as the SAME error type.
NORMALIZERS = [
    (re.compile(r"\buser\s+\S+", re.IGNORECASE), "user <name>"),
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b"), "<ip>"),          # IPv4
    (re.compile(r"\b[0-9a-fA-F:]{3,}\b"), "<hex>"),              # MACs/hashes
    (re.compile(r"\b\d+\b"), "<n>"),                             # bare numbers
]


def normalize(message: str) -> str:
    msg = message.strip()
    for pattern, replacement in NORMALIZERS:
        msg = pattern.sub(replacement, msg)
    # Collapse whitespace so near-identical lines group together
    return re.sub(r"\s+", " ", msg)


def parse_log(path: Path, level_filter: str | None, grep: str | None):
    level_counts: Counter = Counter()
    message_counts: Counter = Counter()
    tag_counts: Counter = Counter()
    total = 0

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            total += 1

            m = LOG_RE.match(line)
            if m:
                level = m.group("level").upper()
                if level == "WARN":
                    level = "WARNING"
                tag = (m.group("tag") or "general").lower()
                msg = normalize(m.group("msg"))
            else:
                level, tag, msg = "UNKNOWN", "general", normalize(line)

            if level_filter and level != level_filter:
                continue
            if grep and grep.lower() not in line.lower():
                continue

            level_counts[level] += 1
            tag_counts[tag] += 1
            message_counts[msg] += 1

    return total, level_counts, tag_counts, message_counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a log file and report top errors/warnings."
    )
    parser.add_argument("logfile", help="Path to the log file")
    parser.add_argument("--top", type=int, default=5,
                        help="Show top N messages (default: 5)")
    parser.add_argument("--level", choices=["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"],
                        help="Only count this severity level")
    parser.add_argument("--pattern",
                        help="Only count lines containing this text (case-insensitive)")
    args = parser.parse_args()

    path = Path(args.logfile)
    if not path.is_file():
        print(f"Error: not a file: {path}", file=sys.stderr)
        return 2

    total, levels, tags, messages = parse_log(path, args.level, args.pattern)

    print(f"File:  {path}")
    print(f"Lines scanned: {total}\n")

    print("By severity:")
    for level, count in levels.most_common():
        print(f"  {level:<8} {count}")
    if not levels:
        print("  (no matching lines)")

    print("\nBy tag:")
    for tag, count in tags.most_common(10):
        print(f"  [{tag}] {count}")

    print(f"\nTop {args.top} messages:")
    for i, (msg, count) in enumerate(messages.most_common(args.top), 1):
        preview = msg if len(msg) <= 100 else msg[:97] + "..."
        print(f"  {i}. ({count}x) {preview}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

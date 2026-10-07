# Python IT Automation

Small, dependency-free Python utilities that automate the tedious parts of IT support work: digging through logs, cleaning up messy folders, and generating compliant passwords. Every script uses only the standard library — no `pip install` needed.

## Scripts

| Script | What it does |
|---|---|
| `log_parser.py` | Parses a log file, counts entries by severity and tag, and prints the top N messages. Normalizes usernames, IPs, and numbers so repeated errors group together (e.g. 200 failed logins from different users count as one error type). Tolerant of malformed lines. |
| `file_organizer.py` | Sorts a messy folder (like Downloads) into subfolders by file type — Documents, Images, Videos, Audio, Archives, Code, Programs. `--dry-run` previews every move first; name collisions get `(1)`, `(2)` suffixes so nothing is overwritten. |
| `password_generator.py` | Generates cryptographically random passwords with the `secrets` module (not `random`). Meets AD default complexity (3 of 4 character classes), skips ambiguous characters like `0`/`O`, optional `--require-all` for 4-class policies. |

## Skills demonstrated

- Python stdlib: `argparse`, `re`, `collections.Counter`, `pathlib`, `shutil`, `secrets`, `ipaddress`
- CLI design: `--dry-run` safety patterns, helpful `--help` text, sane defaults
- Defensive scripting: never overwrites files, skips in-use files, handles malformed input instead of crashing
- Security awareness: `secrets` for credentials, no hardcoded passwords

## What I learned

- Good automation is boring on purpose: preview before acting, never destroy data, log what you did.
- Regex normalization turns a 10,000-line log into 5 actionable error types — that's the difference between reading logs and *understanding* them.
- `secrets` vs `random` matters the moment a script touches credentials.

## How to run

```bash
# Log parser: what keeps failing in this app log?
python3 log_parser.py /var/log/app.log --top 10
python3 log_parser.py app.log --level ERROR --pattern "login"

# File organizer: ALWAYS dry-run first
python3 file_organizer.py ~/Downloads --dry-run
python3 file_organizer.py ~/Downloads

# Password generator
python3 password_generator.py                    # 1 x 16-char password
python3 password_generator.py -n 5 -l 14         # 5 x 14-char passwords
python3 password_generator.py --no-symbols       # letters + digits only
```

Example log parser output:

```
Lines scanned: 6

By severity:
  ERROR    3
  WARNING  1

Top 3 messages:
  1. (3x) Failed login for user <name> from <ip>
  2. (1x) /var is <n>% full
```

> **Pairs with:** `password_generator.py` feeds temporary passwords into `Reset-HDPassword.ps1` from the [powershell-helpdesk-toolkit](../powershell-helpdesk-toolkit) repo — generate here, reset there, share over a secure channel.

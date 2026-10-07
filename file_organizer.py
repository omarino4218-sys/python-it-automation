#!/usr/bin/env python3
"""
File organizer — sort a messy folder (like Downloads) into subfolders by
file extension.

Stdlib only (argparse, pathlib, shutil). Always run with --dry-run first:
it prints exactly what WOULD move where, and moves nothing.

Usage:
    python file_organizer.py ~/Downloads --dry-run
    python file_organizer.py ~/Downloads
    python file_organizer.py ~/Downloads --dest ~/Sorted

Name collisions are handled by appending (1), (2), ... so nothing is
ever overwritten.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Extension -> folder name. Everything else goes in "Other".
CATEGORIES = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
                  ".xls", ".xlsx", ".csv", ".ppt", ".pptx", ".md"},
    "Images":    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
                  ".webp", ".heic", ".tiff"},
    "Videos":    {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"},
    "Audio":     {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Archives":  {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Code":      {".py", ".js", ".html", ".css", ".json", ".xml",
                  ".yml", ".yaml", ".ps1", ".sh", ".java", ".c", ".cpp"},
    "Programs":  {".exe", ".msi", ".dmg", ".pkg", ".deb", ".iso"},
}


def category_for(suffix: str) -> str:
    suffix = suffix.lower()
    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category
    if not suffix:
        return "NoExtension"
    return "Other"


def unique_dest(dest_dir: Path, name: str) -> Path:
    """Return a non-colliding destination path (appends (1), (2), ...)."""
    candidate = dest_dir / name
    if not candidate.exists():
        return candidate
    stem = Path(name).stem
    suffix = Path(name).suffix
    n = 1
    while True:
        candidate = dest_dir / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def organize(source: Path, dest_root: Path, dry_run: bool) -> tuple[int, int]:
    moved, skipped = 0, 0
    # Sort for deterministic output
    files = sorted(
        (p for p in source.iterdir() if p.is_file()),
        key=lambda p: p.name.lower(),
    )
    for item in files:
        category = category_for(item.suffix)
        target_dir = dest_root / category
        target = unique_dest(target_dir, item.name)

        if dry_run:
            print(f"  [DRY-RUN] {item.name} -> {category}/{target.name}")
            moved += 1
            continue

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(target))
            print(f"  Moved: {item.name} -> {category}/{target.name}")
            moved += 1
        except OSError as e:
            print(f"  Skipped (in use?): {item.name} — {e}", file=sys.stderr)
            skipped += 1
    return moved, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sort a messy folder into subfolders by file type."
    )
    parser.add_argument("source", help="Folder to organize (e.g. ~/Downloads)")
    parser.add_argument("--dest", default=None,
                        help="Where to create category folders "
                             "(default: inside source)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would move without moving anything")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        print(f"Error: not a folder: {source}", file=sys.stderr)
        return 2

    dest_root = Path(args.dest).expanduser().resolve() if args.dest else source

    mode = "DRY-RUN — nothing will move" if args.dry_run else "LIVE — moving files"
    print(f"Source: {source}")
    print(f"Destination root: {dest_root}")
    print(f"Mode: {mode}\n")

    moved, skipped = organize(source, dest_root, args.dry_run)

    print(f"\nDone: {moved} file(s) {'would move' if args.dry_run else 'moved'}"
          + (f", {skipped} skipped" if skipped else ""))
    if args.dry_run:
        print("Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

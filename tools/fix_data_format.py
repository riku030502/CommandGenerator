#!/usr/bin/env python3
"""Normalise the markdown tables in a competition data directory.

The parser in ``robocupathome_generator.knowledge`` matches rows of
``maps/location_names.md`` with a regex that requires a *closing* pipe after the
"Object Category" column.  The official CompetitionTemplate ships rows like

    | 1 | bed (p) |

which are missing that closing pipe, so roughly half of the locations silently
disappear and most storage categories are lost.  This script rewrites the table
so every row has all three cells terminated.

Usage:  python3 tools/fix_data_format.py DATA_DIR [--dry-run]
"""

import argparse
import os
import re
import sys

ROW = re.compile(r"^\|\s*\d+\s*\|")
SEP = re.compile(r"^\|[\s:-]+\|[\s:|-]*$")
# "| 13 | cooking table (p) cleaning supplies |" - the pipe between the name and
# the category cell was dropped.  "(p)" always ends the name, so the split point
# is unambiguous.
GLUED = re.compile(r"^(\|\s*\d+\s*\|[^|]*\(p\))\s+([A-Za-z][A-Za-z ]*?)\s*\|\s*$")


def fix_location_table(text: str) -> tuple[str, int]:
    out, changed = [], 0
    for line in text.splitlines():
        stripped = line.rstrip()

        glued = GLUED.match(stripped)
        if glued:
            stripped = f"{glued.group(1)} | {glued.group(2)} |"
            changed += 1

        is_row = bool(ROW.match(stripped))
        is_header = stripped.replace(" ", "").lower().startswith("|number|name|")
        if (is_row or is_header or SEP.match(stripped)) and not stripped.endswith("|"):
            stripped = stripped + " |"
            changed += 1
        # a row that ends with the name cell only: "| 1 | bed (p) |" -> add empty category
        if is_row and stripped.count("|") == 3:
            stripped = stripped + " |"
            changed += 1
        out.append(stripped)
    return "\n".join(out) + "\n", changed


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("data_dir", help="competition data directory")
    p.add_argument("--dry-run", action="store_true", help="only report, do not write")
    args = p.parse_args()

    path = os.path.join(args.data_dir, "maps", "location_names.md")
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    with open(path, encoding="utf-8") as fh:
        original = fh.read()
    fixed, changed = fix_location_table(original)

    if changed == 0:
        print(f"OK: {path} already in the expected format")
        return 0
    if args.dry_run:
        print(f"WOULD FIX: {path} ({changed} cell(s) terminated)")
        return 0

    with open(path + ".bak", "w", encoding="utf-8") as fh:
        fh.write(original)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(fixed)
    print(f"FIXED: {path} ({changed} cell(s) terminated); backup at {path}.bak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

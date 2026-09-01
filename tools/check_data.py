#!/usr/bin/env python3
"""Validate a competition data directory before running the generator.

Counts the rows actually present in the markdown tables, compares them with what
``robocupathome_generator.knowledge.parse_data`` manages to extract, and reports
any entry that the parser silently dropped.  Finally it generates a few sample
commands so you can eyeball the result.

Usage:  python3 tools/check_data.py DATA_DIR [-n SAMPLES]
"""

import argparse
import os
import re
import sys

REQUIRED = [
    "names/names.md",
    "maps/location_names.md",
    "maps/room_names.md",
    "objects/objects.md",
]


def _rows(path: str) -> list[str]:
    """Data rows of a markdown table (header and separator lines excluded)."""
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s:|-]+\|?$", line):
            continue
        rows.append(line)
    return rows[1:] if rows else []


def _report(label: str, declared: int, parsed: list, problems: list[str],
            hint: str = "") -> None:
    mark = "ok " if declared == len(parsed) else "!! "
    print(f"{mark}{label:<22} table rows: {declared:>3}   parsed: {len(parsed):>3}")
    if declared != len(parsed):
        msg = f"{label}: {declared} row(s) in the markdown table but {len(parsed)} parsed"
        problems.append(f"{msg}\n      {hint}" if hint else msg)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("data_dir")
    p.add_argument("-n", "--samples", type=int, default=5,
                   help="number of sample commands to print (default 5)")
    args = p.parse_args()

    missing = [f for f in REQUIRED if not os.path.isfile(os.path.join(args.data_dir, f))]
    if missing:
        print(f"ERROR: {args.data_dir} is missing:", file=sys.stderr)
        for f in missing:
            print(f"  - {f}", file=sys.stderr)
        return 1

    from robocupathome_generator.knowledge import parse_data
    from robocupathome_generator.gpsr_commands import CommandGenerator

    k = parse_data(args.data_dir)
    problems: list[str] = []   # break command generation
    warnings: list[str] = []   # worth knowing, but generation still works

    print(f"data dir: {os.path.abspath(args.data_dir)}\n")
    _report("names", len(_rows(f"{args.data_dir}/names/names.md")), k.names, problems,
            "a name must be a single word made of letters only (no space, digit or hyphen)")
    _report("rooms", len(_rows(f"{args.data_dir}/maps/room_names.md")), k.rooms, problems,
            "a room name must be one or two words made of letters only")

    loc_rows = [r for r in _rows(f"{args.data_dir}/maps/location_names.md")
                if re.match(r"^\|\s*\d+\s*\|", r)]
    _report("locations", len(loc_rows), k.locations, problems,
            "a location name may only contain letters, spaces and the '(p)' marker, "
            "and every row must end with '|'\n      "
            "try: python3 tools/fix_data_format.py " + args.data_dir)

    obj_src = open(f"{args.data_dir}/objects/objects.md", encoding="utf-8").read()
    declared_classes = len(re.findall(r"^# Class\s+", obj_src, re.MULTILINE))
    _report("object categories", declared_classes, k.categories, problems,
            "each class header must look like '# Class plural_name (singular_name)'")
    print(f"   objects: {len(k.objects)}   placement locations: "
          f"{len(k.placement_locations)}   storage categories: {len(k.storages)}")

    declared_placements = sum(1 for r in loc_rows if "(p)" in r)
    if declared_placements != len(k.placement_locations):
        problems.append(
            f"placement locations: {declared_placements} row(s) marked (p) but "
            f"{len(k.placement_locations)} parsed"
        )

    if not k.placement_locations:
        problems.append("no placement location: mark at least one location with '(p)'")
    if not k.storages:
        problems.append("no storage category: fill the 'Object Category' column")

    unknown = sorted(set(k.storages) - set(k.object_categories_plural))
    if unknown:
        warnings.append(
            "the 'Object Category' column of maps/location_names.md names "
            f"{unknown}, which is not a class in objects/objects.md\n"
            f"      known classes: {k.object_categories_plural}\n"
            "      GPSR generation is unaffected; this matters for Storing Groceries"
        )

    multiword = [n for n in k.names if " " in n]
    if multiword:
        problems.append(f"names must be a single word, found: {multiword}")

    print()
    if problems:
        print("PROBLEMS")
        for msg in problems:
            print(f"  - {msg}")
    else:
        print("PROBLEMS: none")

    if warnings:
        print("\nWARNINGS (generation still works)")
        for msg in warnings:
            print(f"  - {msg}")

    if args.samples > 0:
        gen = CommandGenerator(k)
        print(f"\nsample commands ({args.samples})")
        for _ in range(args.samples):
            c = gen.generate_command_start(cmd_category="")
            print("  " + c[0].upper() + c[1:])

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

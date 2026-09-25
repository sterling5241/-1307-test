#!/usr/bin/env python3
"""
Issue #1307 tester
Runs both allow_delete=true and allow_delete=false cases
"""

import sys
from pathlib import Path
from configupdater import ConfigUpdater

config_path = Path(__file__).parent / "config.txt"
if not config_path.exists():
    print("ERROR: config.txt not found")
    sys.exit(1)

text = config_path.read_text(encoding="utf-8")

def extract_block(text, start_marker, end_marker=None):
    try:
        start = text.index(start_marker) + len(start_marker)
        if end_marker:
            end = text.index(end_marker, start)
        else:
            end = len(text)
        return text[start:end].strip()
    except ValueError:
        return ""

def parse_case(block):
    base = ""
    overrides = ""
    if "----- BASE -----" in block:
        base = extract_block(block, "----- BASE -----", "----- OVERRIDES -----")
    if "----- OVERRIDES -----" in block:
        overrides = extract_block(block, "----- OVERRIDES -----")
    return base.strip(), overrides.strip()

# -------------------------------------------------
# Helper
# -------------------------------------------------
def has_deleted_value(section):
    for entry in section:
        value = section.get(entry, None)
        if value and str(value.value).strip() == '__DELETED__':
            return True
    return False

# -------------------------------------------------
# OLD
# -------------------------------------------------
def apply_old(base_text, overrides_text, allow_delete_section):
    base = ConfigUpdater(strict=False, allow_no_value=True,
                         space_around_delimiters=False, delimiters=(":", "="))
    base.read_string(base_text)

    overrides = ConfigUpdater(strict=False, allow_no_value=True,
                              space_around_delimiters=False, delimiters=(":", "="))
    overrides.read_string(overrides_text)

    for section_name in overrides.sections():
        section = overrides.get_section(section_name)
        section_action = section.get('__action__', None)

        if section_action and str(section_action.value).strip() == 'DELETED':
            if allow_delete_section and base.has_section(section_name):
                del base[section_name]
            continue

        if base.has_section(section_name):
            for key in list(section.keys()):
                val = str(section[key].value).strip() if section[key].value else ""
                if val == "__DELETED__":
                    if key in base[section_name]:
                        del base[section_name][key]
                else:
                    base[section_name][key] = section[key].value
        else:
            # OLD: always add
            new_section = section.detach()
            last = list(base.sections())[-1] if base.sections() else None
            if last:
                base[last].add_after.section(new_section)
            else:
                base.add_section(new_section)

    return str(base).strip()

# -------------------------------------------------
# NEW
# -------------------------------------------------
def apply_new(base_text, overrides_text, allow_delete_section):
    base = ConfigUpdater(strict=False, allow_no_value=True,
                         space_around_delimiters=False, delimiters=(":", "="))
    base.read_string(base_text)

    overrides = ConfigUpdater(strict=False, allow_no_value=True,
                              space_around_delimiters=False, delimiters=(":", "="))
    overrides.read_string(overrides_text)

    for section_name in overrides.sections():
        section = overrides.get_section(section_name)
        section_action = section.get('__action__', None)

        if section_action and str(section_action.value).strip() == 'DELETED':
            if allow_delete_section and base.has_section(section_name):
                del base[section_name]
            continue

        if base.has_section(section_name):
            for key in list(section.keys()):
                val = str(section[key].value).strip() if section[key].value else ""
                if val == "__DELETED__":
                    if key in base[section_name]:
                        del base[section_name][key]
                else:
                    base[section_name][key] = section[key].value
        else:
            # NEW: only add if no __DELETED__
            if not has_deleted_value(section):
                new_section = section.detach()
                last = list(base.sections())[-1] if base.sections() else None
                if last:
                    base[last].add_after.section(new_section)
                else:
                    base.add_section(new_section)

    return str(base).strip()

# -------------------------------------------------
# Run both cases
# -------------------------------------------------
case1 = extract_block(text, "===== CASE 1: allow_delete = true =====", "===== CASE 2:")
case2 = extract_block(text, "===== CASE 2: allow_delete = false =====")

base1, overrides1 = parse_case(case1)
base2, overrides2 = parse_case(case2)

print("============================================================")
print("CASE 1: allow_delete_section = true")
print("============================================================")
print("----- BASE -----")
print(base1)
print()
print("----- OVERRIDES -----")
print(overrides1)
print()
print("===== OLD (broken) =====")
print(apply_old(base1, overrides1, allow_delete_section=True))
print()
print("===== NEW (fixed) =====")
print(apply_new(base1, overrides1, allow_delete_section=True))
print()

print("============================================================")
print("CASE 2: allow_delete_section = false")
print("============================================================")
print("----- BASE -----")
print(base2)
print()
print("----- OVERRIDES -----")
print(overrides2)
print()
print("===== OLD (broken) =====")
print(apply_old(base2, overrides2, allow_delete_section=False))
print()
print("===== NEW (fixed) =====")
print(apply_new(base2, overrides2, allow_delete_section=False))
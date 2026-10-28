#!/usr/bin/env python3
"""Source scan for hidden-test compatibility risks in Kaggle notebooks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VISIBLE_TEST_WELLS = ("000d7d20", "00bbac68", "00e12e8b")
VISIBLE_TEST_ROW_COUNTS = ("14151", "3836", "6014", "4301")


def load_code_text(path: Path) -> tuple[str, dict]:
    if not path.is_file():
        raise FileNotFoundError(path)

    if path.suffix == ".ipynb":
        nb = json.loads(path.read_text(encoding="utf-8"))
        code_cells = []
        markdown_cells = 0
        for cell in nb.get("cells", []):
            source = "".join(cell.get("source", []))
            if cell.get("cell_type") == "code":
                code_cells.append(source)
            elif cell.get("cell_type") == "markdown":
                markdown_cells += 1
        return "\n\n".join(code_cells), {
            "kind": "ipynb",
            "code_cells": len(code_cells),
            "markdown_cells": markdown_cells,
        }

    return path.read_text(encoding="utf-8"), {"kind": path.suffix.lstrip(".") or "text"}


def find_patterns(text: str, patterns: dict[str, str]) -> list[dict]:
    hits = []
    lines = text.splitlines()
    for name, pattern in patterns.items():
        regex = re.compile(pattern)
        for i, line in enumerate(lines, 1):
            if regex.search(line):
                hits.append({"name": name, "line": i, "text": line.strip()[:240]})
    return hits


def audit(path: Path) -> dict:
    text, meta = load_code_text(path)
    lower = text.lower()

    hard_fail_patterns = {
        "hardcoded_visible_test_well": r"\b(?:%s)\b" % "|".join(VISIBLE_TEST_WELLS),
        "hardcoded_visible_test_row_count": r"\b(?:%s)\b" % "|".join(VISIBLE_TEST_ROW_COUNTS),
        "unsafe_train_test_tvtinput_row_copy": r"TVT_input[\"'\]]*\s*=\s*.*TVT_input.*\.values",
        "static_submission_replay_name": r"read_csv\([^)]*submission\.csv[^)]*\).*to_csv\([^)]*submission\.csv",
    }

    warn_patterns = {
        "fixed_width_id_slice": r"\.str\[[0-9]+:[0-9]*\]|\.str\[:[0-9]+\]",
        "iloc_id_position_mapping": r"iloc\[[^\]]+\].*id|id.*iloc\[[^\]]+\]",
        "hardcoded_kaggle_working_submission_read": r"read_csv\([^)]*/kaggle/working/submission\.csv",
    }

    required_signals = {
        "sample_submission": "sample_submission" in lower,
        "dynamic_horizontal_well_discovery": bool(
            re.search(r"glob\([^)]*horizontal_well|\.glob\([^)]*horizontal_well", text)
        ),
        "test_split_reference": bool(re.search(r"['\"]test['\"]|/test/", text)),
        "submission_write": "submission.csv" in lower and ".to_csv" in lower,
    }

    failures = find_patterns(text, hard_fail_patterns)
    warnings = find_patterns(text, warn_patterns)
    missing_required = [name for name, ok in required_signals.items() if not ok]

    if missing_required:
        warnings.append({
            "name": "missing_required_signal",
            "line": None,
            "text": ", ".join(missing_required),
        })

    return {
        "status": "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS",
        "path": str(path),
        **meta,
        "required_signals": required_signals,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Notebook or Python source path")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON output path")
    args = parser.parse_args()

    result = audit(args.path)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")

    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate and atomically seal one complete Frontier review subject."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from frontier_review import prepare_review


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        draft = json.loads(arguments.draft.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "status": "NOT_READY",
            "findings": [{"code": "DRAFT_UNREADABLE", "message": str(exc)}],
        }
    else:
        result = prepare_review(draft, arguments.project_root, arguments.output_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "SEALED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""`python manage.py system_audit` — run the AI gap analyzer from Django.

Hosts the standalone analyzer (`tools/gap_analyzer.py`) so it can also be
run inside the deployed backend where a UI/endpoint might call it later.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from django.core.management.base import BaseCommand

TOOLS_DIR = Path(__file__).resolve().parents[5] / "tools"


class Command(BaseCommand):
    help = "Run the AI gap analyzer and write docs/AI_GAP_REPORT.md (+.json)."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--llm", action="store_true", help="force LLM mode")
        parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
        parser.add_argument(
            "--base-url",
            default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        parser.add_argument("--json", action="store_true", help="print raw JSON report only")

    def handle(self, *args, **options) -> None:
        if not TOOLS_DIR.exists():
            self.stderr.write(f"tools/ directory not found at {TOOLS_DIR}")
            raise SystemExit(1)
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        import gap_analyzer as ga

        argv = []
        if options.get("llm"):
            argv.append("--llm")
        argv += ["--model", options["model"]]
        base_url = options.get("base_url") or options.get("base-url") or os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        argv += ["--base-url", base_url]
        if options.get("json"):
            argv.append("--json")
        raise SystemExit(ga.main(argv))
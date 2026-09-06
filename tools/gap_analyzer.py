"""AI gap analyzer for the Perfect Foundation SMS project.

Scans the frontend + backend trees, inventories features and integrations,
then produces a prioritized "what to add / what not to add" report.

Modes
-----
- heuristic (default, offline): rule-based scoring against a curated
  capability checklist.
- llm (auto when OPENAI_API_KEY is set, or forced via --llm): sends the
  inventory + heuristic findings to an OpenAI-compatible chat-completions
  endpoint and asks for a structured add/don't-add report.

Usage
-----
    python tools/gap_analyzer.py            # offline heuristic
    OPENAI_API_KEY=... python tools/gap_analyzer.py        # auto LLM
    python tools/gap_analyzer.py --llm --model gpt-4o-mini # forced

Outputs
-------
    docs/AI_GAP_REPORT.md, docs/AI_GAP_REPORT.json, console summary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"
OUT_DIR = ROOT / "docs"

CHAT_ENDPOINT = "/chat/completions"


def _scan_dir(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(p for p in path.glob("**/*") if p.is_file())


def inventory_backend() -> dict:
    apps_dir = BACKEND / "apps"
    apps = {}
    for app in sorted(d for d in apps_dir.iterdir() if d.is_dir() and d.name != "__pycache__"):
        models_path = app / "models.py"
        urls_path = app / "urls.py"
        models = []
        if models_path.exists():
            for line in models_path.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"^class\s+(\w+)", line)
                if m:
                    models.append(m.group(1))
        endpoints = []
        if urls_path.exists():
            text = urls_path.read_text(encoding="utf-8", errors="replace")
            endpoints = re.findall(
                r'(?:path|re_path)\(\s*["\']([^"\']+)["\']', text, flags=re.DOTALL
            )
        apps[app.name] = {"models": models, "endpoints": endpoints}
    return {"apps": apps}


def inventory_frontend() -> dict:
    app_jsx = SRC / "App.jsx"
    routes = []
    if app_jsx.exists():
        text = app_jsx.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'path=\{?["\']([^"\']+)["\']', text):
            routes.append(m.group(1))
    pages = {}
    api_calls: set[str] = set()
    for page in sorted(glob_path(SRC / "pages", "*.jsx")):
        text = page.read_text(encoding="utf-8", errors="replace")
        pages[page.stem] = {"lines": len(text.splitlines())}
        api_calls.update(re.findall(r'["\'`](/api/[A-Za-z0-9_/:{}.\-]+)', text))
    for extra in sorted(glob_path(SRC, "*.jsx")) + sorted(glob_path(SRC, "*.js")):
        if extra.name in ("main.jsx", "sessionWatch.js") or extra.parent != SRC:
            continue
        text = extra.read_text(encoding="utf-8", errors="replace")
        api_calls.update(re.findall(r'["\'`](/api/[A-Za-z0-9_/:{}.\-]+)', text))

    all_files = sorted(
        glob_path(SRC, "*.jsx") + glob_path(SRC, "*.js") + glob_path(SRC / "pages", "*.jsx")
    )
    page_files = {p.stem: p for p in glob_path(SRC / "pages", "*.jsx")}
    all_text = {str(p): p.read_text(encoding="utf-8", errors="replace") for p in all_files}
    referenced = set()
    for stem, path in page_files.items():
        for other, text in all_text.items():
            if Path(other) == path:
                continue
            if re.search(rf"\b{re.escape(stem)}\b", text):
                referenced.add(stem)
                break
    orphaned = sorted(set(page_files) - referenced)

    ai_keywords = (r"openai|gpt-?|anthropic|claude|gemini|llama|openrouter"
                   r"|langchain|aistudio|/api/ai|\.ai\b")
    ar = " ".join(p.read_text(encoding="utf-8", errors="replace")
                  for p in glob_path(SRC / "pages", "*.jsx") + glob_path(SRC, "*.jsx"))
    has_ai = bool(re.search(ai_keywords, ar, flags=re.IGNORECASE))
    return {
        "routes": routes,
        "pages": pages,
        "page_count": len(pages),
        "api_call_count": len(api_calls),
        "orphaned_pages": orphaned,
        "has_ai": has_ai,
        "sample_api_calls": sorted(api_calls),
    }


def glob_path(base: Path, pattern: str) -> list[Path]:
    return sorted(p for p in base.glob(pattern) if p.is_file())


def scan_integrations() -> dict:
    keywords = {
        "stripe": "online payment (Stripe)",
        "twilio": "SMS provider (Twilio)",
        "jazzcash": "wallet: JazzCash",
        "easypaisa": "wallet: EasyPaisa",
        "openai": "LLM / AI provider",
        "reportlab": "PDF generation",
        "vercel_blob": "file storage",
        "pyotp": "2FA / TOTP",
        "google_sso": "Google SSO",
    }
    found = {}
    for path in _scan_dir(BACKEND / "apps"):
        if path.suffix != ".py" or "migrations" in path.parts:
            continue
        if path.name.startswith(("system_audit", "gap_analyzer")):
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for key, label in keywords.items():
            if key in text:
                found.setdefault(label, []).append(
                    str(path.relative_to(ROOT)).replace("\\", "/")
                )
    return {label: files for label, files in found.items()}


CHECKLIST = [
    {
        "category": "AI & smart features",
        "signals": [
            ("integration", "LLM / AI provider"),
            ("frontend_ai", "has_ai"),
            ("path_api", "/api/ai"),
        ],
        "why_add": "No AI anywhere today; AI drafts feedback, alerts, reports, and smart search.",
        "why_skip": "Add only after core modules are surfaced; keep it augmentation, not a platform.",
    },
    {
        "category": "Online payment (wallets)",
        "signals": [
            ("integration", "stripe"),
            ("integration", "wallet: JazzCash"),
            ("integration", "wallet: EasyPaisa"),
            ("frontend", "stripe"),
            ("frontend", "jazzcash"),
        ],
        "why_add": "JazzCash/EasyPaisa backends are complete but not wired into the UI.",
        "why_skip": "Do not add PayPal or a 4th provider until existing wallet UIs ship.",
    },
    {
        "category": "Workflow / approvals",
        "signals": [
            ("app_models", "workflow"),
            ("app_routes", "workflow"),
            ("frontend_route", "approval"),
        ],
        "why_add": "Workflow engine is complete but its UI is unrouted; surfaces approvals per role.",
        "why_skip": "No new engine work needed — only navigation.",
    },
    {
        "category": "Notifications & messaging",
        "signals": [
            ("app_models", "communication"),
            ("integration", "SMS provider (Twilio)"),
            ("frontend", "notifications"),
            ("app_routes", "communication"),
        ],
        "why_add": "Queue + cron exist; add WhatsApp/email channels and push (PWA) next.",
        "why_skip": "Do not rebuild the queue or add a 2nd SMS provider.",
    },
    {
        "category": "Reporting & analytics",
        "signals": [
            ("app_models", "reports"),
            ("app_routes", "reports"),
            ("frontend", "report-builder"),
            ("frontend", "dashboard"),
        ],
        "why_add": "~150 endpoints + builder exist; reduce to the surfaced catalog (ReportsCenter).",
        "why_skip": "No new BI/ETL pipeline or separate analytics DB at this scale.",
    },
    {
        "category": "Auth & security",
        "signals": [
            ("app_models", "accounts"),
            ("integration", "2FA / TOTP"),
            ("integration", "Google SSO"),
            ("frontend", "2fa"),
        ],
        "why_add": "Nothing critical; consider admin 2FA enforcement + IP allowlists if audited.",
        "why_skip": "Do not build another auth system — SSO, 2FA, lockout already exist.",
    },
    {
        "category": "Finance automation",
        "signals": [
            ("app_models", "finance"),
            ("app_routes", "finance"),
            ("frontend", "finance"),
            ("integration", "PDF generation"),
        ],
        "why_add": "Fee reminder scheduling visible in UI + late-fee previews would close the loop.",
        "why_skip": "Accountancy ledgers, budgets, and reconciliations already exist.",
    },
    {
        "category": "Student/parent mobile",
        "signals": [
            ("frontend_route", "parent-portal"),
            ("frontend_file", "sw.js"),
            ("app_routes", "portal"),
        ],
        "why_add": "PWA offline + push for fees/attendance are the biggest parent-facing wins.",
        "why_skip": "A full native app is overkill while the PWA is dormant.",
    },
    {
        "category": "Timetable management",
        "signals": [
            ("app_models", "timetable"),
            ("app_routes", "timetable"),
            ("frontend", "timetable"),
        ],
        "why_add": "Add manual entry editing (view/generate exist).",
        "why_skip": "Auto-generation exists; do not swap the engine.",
    },
    {
        "category": "Data import / export",
        "signals": [
            ("app_routes", "reports"),
            ("frontend", "data-import"),
            ("frontend", "data-export"),
        ],
        "why_add": "Extend UI import beyond students/teachers to the backend catalog.",
        "why_skip": "Backend import engine already exists; don't rebuild it.",
    },
]


def _app_scans(inv: dict):
    apps = inv["backend"]["apps"]
    return {
        app: {
            "models": set(data.get("models", [])),
            "endpoints": data.get("endpoints", []),
        }
        for app, data in apps.items()
    }


def evaluate_checklist(inv: dict, integrations: dict) -> list[dict]:
    apps = _app_scans(inv)
    fe = inv["frontend"]
    joined = "\n".join(fe["sample_api_calls"])
    all_models = set()
    for a in apps.values():
        all_models |= a["models"]
    all_routes = set()
    for a in apps.values():
        all_routes.update(a["endpoints"])

    def has(signal) -> bool:
        kind, value = signal
        if kind == "integration":
            return any(value in label for label in integrations)
        if kind == "frontend_route":
            return any(value in f"/{r}" for r in fe.get("routes", []))
        if kind == "frontend_file":
            return bool(list(FRONTEND.rglob(value)))
        if kind == "frontend_ai":
            return bool(fe.get("has_ai"))
        if kind == "frontend":
            return value in joined or any(value == r for r in fe.get("routes", []))
        if kind == "app_models":
            app = apps.get(value)
            return bool(app and app["models"])
        if kind == "app_routes":
            app = apps.get(value)
            return bool(app and app["endpoints"])
        if kind == "frontend_page":
            return value in fe.get("pages", {})
        if kind == "path_api":
            return value in joined
        return False

    results = []
    for item in CHECKLIST:
        score = 0
        matched = []
        for signal in item["signals"]:
            if has(signal):
                score += 1
                matched.append(signal)
        total = len(item["signals"])
        status = "complete" if score == total else ("partial" if score else "missing")
        results.append(
            {
                "category": item["category"],
                "status": status,
                "signal_score": score,
                "signal_total": total,
                "matched": matched,
                "signals": item["signals"],
                "add": f"ADD - {item['why_add']}" if status != "complete" else "OK",
                "skip": item["why_skip"],
            }
        )
    return results


CURATED_FINDINGS = [
    {
        "finding": "JazzCash/EasyPaisa backends built but unused by the UI",
        "add": True,
        "reason": "Wire to UI or remove the labels; server code is complete (hash + callbacks).",
    },
    {
        "finding": "Workflow engine UI orphaned (no routes/nav)",
        "add": True,
        "reason": "Surface PendingApprovals/definitions; engine is done, navigation is missing.",
    },
    {
        "finding": "ReportsCenter.jsx unreferenced dead code",
        "add": False,
        "reason": "Pick ReportsPage or ReportsCenter catalog; ship one, delete the other.",
    },
    {
        "finding": "No AI features in frontend or backend",
        "add": True,
        "reason": "Add AI drafting/smart-search/prediction layers on existing data models.",
    },
    {
        "finding": "Email delivery depends on DJANGO_EMAIL_* (unset)", 
        "add": True,
        "reason": "Configure an SMTP send provider or document SMS-first messaging.",
    },
    {
        "finding": "Frontend data import covers only students+teachers",
        "add": True,
        "reason": "Extend to the backend's import catalog; no new engine needed.",
    },
    {
        "finding": "Stripe is the only wired online payment path",
        "add": False,
        "reason": "Finish J/E wallets first; avoid adding more providers.",
    },
    {
        "finding": "Multi-tenancy + campus isolation already enforced in ORM",
        "add": False,
        "reason": "Do not redesign the tenancy layer.",
    },
    {
        "finding": "Auth stack is comprehensive (SSO, 2FA, lockout, password history)",
        "add": False,
        "reason": "Do not build another auth system.",
    },
]


def build_inventory() -> dict:
    return {
        "backend": inventory_backend(),
        "frontend": inventory_frontend(),
        "integrations": scan_integrations(),
    }


def build_heuristic(inv: dict) -> dict:
    check = evaluate_checklist(inv, inv["integrations"])
    add = [f for f in CURATED_FINDINGS if f["add"]]
    skip = [f for f in CURATED_FINDINGS if not f["add"]]
    return {"checklist": check, "curated_add": add, "curated_skip": skip}


def build_markdown(inventory: dict, analysis: dict) -> str:
    fe = inventory["frontend"]
    be = inventory["backend"]
    apps = be["apps"]
    lines = [
        "# AI Gap Report — Perfect Foundation SMS",
        "",
        f"Generated by `tools/gap_analyzer.py` · {__import__('datetime').datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## 1. Inventory snapshot",
        "",
        f"- Backend apps: **{len(apps)}** · models/classes: **{sum(len(a['models']) for a in apps.values())}**",
        f"- Backend URL routes: **{sum(len(a['endpoints']) for a in apps.values())}**",
        f"- Frontend pages: **{fe['page_count']}** · routed paths: **{len(fe['routes'])}**",
        f"- Frontend-distinct API calls: **{fe['api_call_count']}**",
        f"- Orphaned frontend pages: **{', '.join(fe['orphaned_pages']) or 'none'}**",
        "",
        "## 2. Integrations detected",
        "",
    ]
    if inventory["integrations"]:
        for label, files in inventory["integrations"].items():
            lines.append(f"- **{label}** (`{files[0]}`)")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## 3. Capability checklist")
    lines.append("")
    lines.append("| Category | Status | Signals | Recommendation |")
    lines.append("| --- | --- | --- | --- |")
    for row in analysis["checklist"]:
        lines.append(
            f"| {row['category']} | {row['status']} ({row['signal_score']}/{row['signal_total']}) "
            f"| {', '.join(s[1] for s in row['matched']) or '—'} | {row['add']} |"
        )
    lines.append("")
    lines.append("## 4. What to ADD")
    lines.append("")
    for f in analysis["curated_add"]:
        lines.append(f"- **{f['finding']}** — {f['reason']}")
    lines.append("")
    lines.append("## 5. What NOT to add (cut / avoid)")
    lines.append("")
    for f in analysis["curated_skip"]:
        lines.append(f"- **{f['finding']}** — {f['reason']}")
    lines.append("")
    lines.append("## 6. Method")
    lines.append("")
    lines.append("Inventory is parsed statically (routes, models, endpoints, API calls, integrations). "
                 "Heuristic scoring compares signals per capability. In `--llm` mode an LLM refines the "
                 "recommendations from this same evidence.")
    lines.append("")
    return "\n".join(lines)


def call_llm(inventory: dict, analysis: dict, api_key: str, base_url: str, model: str) -> str:
    import urllib.request

    prompt = (
        "You audit a school management ERP (Django+DRF backend, React frontend). "
        "Evidence below is static inventory + a heuristic checklist. "
        "Produce a concise prioritized list of (1) features to ADD next with reasons, and "
        "(2) features NOT to add with reasons. Be specific, avoid generic advice, and stay strictly "
        "within evidence. Return JSON: {\"add\":[{\"item\":string,\"reason\":string}],"
        "\"skip\":[{\"item\":string,\"reason\":string}]}. No prose outside JSON.\n\n"
        f"INVENTORY:\n{json.dumps(inventory, default=str)[:14000]}\n\n"
        f"HEURISTIC:\n{json.dumps(analysis, default=str)[:6000]}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a pragmatic product engineer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    url = base_url.rstrip("/") + CHAT_ENDPOINT
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = json.loads(resp.read().decode())
    return body["choices"][0]["message"]["content"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI gap analyzer for Perfect Foundation SMS")
    parser.add_argument("--llm", action="store_true", help="force LLM mode")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--json", action="store_true", help="print raw JSON report only")
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    analysis = build_heuristic(inventory)

    llm_text = None
    if args.llm or (args.api_key and not args.json):
        if not args.api_key:
            print("OPENAI_API_KEY not set — running offline heuristic mode.", file=sys.stderr)
        else:
            try:
                llm_text = call_llm(inventory, analysis, args.api_key, args.base_url, args.model)
                llm_obj = json.loads(llm_text)
                analysis["llm"] = llm_obj
            except Exception as exc:  # noqa: BLE001
                print(f"LLM call failed ({exc}); falling back to heuristic.", file=sys.stderr)

    report_json = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "inventory": inventory,
        "analysis": analysis,
    }
    if args.json:
        print(json.dumps(report_json, indent=2))
        return 0

    markdown = build_markdown(inventory, analysis)
    if llm_text:
        markdown += "\n\n## 7. LLM recommendation\n\n" + llm_text + "\n"
    out_md = OUT_DIR / "AI_GAP_REPORT.md"
    out_json = OUT_DIR / "AI_GAP_REPORT.json"
    out_md.write_text(markdown, encoding="utf-8")
    out_json.write_text(json.dumps(report_json, indent=2), encoding="utf-8")

    print(f"Wrote {out_md.relative_to(ROOT)} and {out_json.relative_to(ROOT)}")
    print(f"Backend apps: {len(inventory['backend']['apps'])} | "
          f"models: {sum(len(a['models']) for a in inventory['backend']['apps'].values())} | "
          f"routes: {sum(len(a['endpoints']) for a in inventory['backend']['apps'].values())}")
    print(f"Frontend pages: {len(inventory['frontend']['pages'])} | "
          f"api calls: {inventory['frontend']['api_call_count']} | "
          f"orphans: {', '.join(inventory['frontend']['orphaned_pages']) or 'none'}")
    print("Checklist status:")
    for row in analysis["checklist"]:
        print(f"  [{row['status']:<8}] {row['category']} ({row['signal_score']}/{row['signal_total']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
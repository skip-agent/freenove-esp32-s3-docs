#!/usr/bin/env python3
"""Scoped ESP32-project access to the existing Sam Hindsight bank."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import shlex
import subprocess
import sys
import time
from urllib.parse import quote

HOST = "mac-mini"
BASE = "http://127.0.0.1:8888"
BANK = "sam-personal"
STRATEGY = "esp32-project-lessons"
MODEL_ID = "esp32-project-learning-journey"

RETAIN_MISSION = (
    "Extract only durable ESP32-project learning facts: concepts the learner understood, "
    "verified hardware or IDE setup, lesson-specific corrections or missing steps, "
    "recurring confusion, and incidents with root cause, fix, and guardrail. Ignore "
    "greetings, transient confirmations, raw chat, full logs, secrets, credentials, "
    "and speculation. Preserve exact verified UI labels, board and chip names, URLs, "
    "and versions. Mark uncertainty explicitly."
)

SOURCE_QUERY = (
    "Summarize verified ESP32-S3 project learning progress, setup, lesson corrections, recurring "
    "confusion, and stable coaching preferences. Use the available ESP32-project observations. "
    "Organize by lesson ID, distinguish learner state from webpage edits, and label open "
    "blockers or uncertainty. Exclude transient chat and unrelated material."
)

_LOCAL_HINDSIGHT: bool | None = None


def _use_local() -> bool:
    """True when Hindsight answers on localhost (i.e. we are on the mini itself).

    Probed once and cached. Off the mini (e.g. Galen's laptop) this is False and
    requests tunnel over `ssh mac-mini`, so the helper works from any machine that
    has the `mac-mini` SSH alias.
    """
    global _LOCAL_HINDSIGHT
    if _LOCAL_HINDSIGHT is None:
        probe = subprocess.run(
            ["curl", "-fsS", "-m", "2", "-o", "/dev/null", f"{BASE}/health"],
            capture_output=True,
            text=True,
        )
        _LOCAL_HINDSIGHT = probe.returncode == 0
    return _LOCAL_HINDSIGHT


def _request(method: str, path: str, payload: dict | None = None, *, check: bool = True):
    url = f"{BASE}{path}"
    command = f"curl -fsS -X {method} {shlex.quote(url)}"
    stdin = None
    if payload is not None:
        command += " -H 'Content-Type: application/json' --data-binary @-"
        stdin = json.dumps(payload)
    argv = ["sh", "-c", command] if _use_local() else ["ssh", HOST, command]
    proc = subprocess.run(
        argv, input=stdin, text=True, capture_output=True
    )
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"request failed: {method} {path}")
    if proc.returncode:
        return None
    text = proc.stdout.strip()
    return json.loads(text) if text else {}


def _bank_path(suffix: str) -> str:
    return f"/v1/default/banks/{BANK}{suffix}"


def ensure(_: argparse.Namespace) -> None:
    current = _request("GET", _bank_path("/config"))
    config = current.get("config", {})
    strategies = dict(config.get("retain_strategies") or {})
    strategies.pop("tinyskiff-lessons", None)  # remove the incorrectly named predecessor
    strategies[STRATEGY] = {
        "retain_extraction_mode": "concise",
        "retain_chunk_size": 3000,
        "retain_mission": RETAIN_MISSION,
    }
    # Add only a named strategy. Never overwrite sam-personal's global defaults,
    # missions, model routes, or observation settings for a project integration.
    _request("PATCH", _bank_path("/config"), {
        "updates": {"retain_strategies": strategies}
    })

    trigger = {
        "mode": "full",
        # Hindsight 0.8.4 refreshes saved mental models with a low reflect budget,
        # which can return no facts even when scoped mid-budget reflection succeeds.
        # Keep the model definition, but use `journey` until that bug is fixed.
        "refresh_after_consolidation": False,
        "refresh_cron": None,
        "fact_types": ["world", "experience", "observation"],
        "exclude_mental_models": True,
        "tags_match": "all_strict",
        "include_chunks": False,
        "recall_max_tokens": 4096,
        "recall_chunks_max_tokens": 0,
    }
    payload = {
        "name": "ESP32 Project Learning Journey",
        "source_query": SOURCE_QUERY,
        "tags": ["esp32-project", "learning"],
        "max_tokens": 4096,
        "trigger": trigger,
    }
    existing = _request("GET", _bank_path(f"/mental-models/{MODEL_ID}"), check=False)
    if existing is None:
        result = _request("POST", _bank_path("/mental-models"), {"id": MODEL_ID, **payload})
    else:
        result = _request("PATCH", _bank_path(f"/mental-models/{MODEL_ID}"), payload)
    operation_id = (result or {}).get("operation_id")
    if operation_id:
        for _ in range(60):
            op = _request("GET", _bank_path(f"/operations/{operation_id}"))
            if op.get("status") in {"completed", "failed", "cancelled"}:
                break
            time.sleep(1)
    status(argparse.Namespace())


def recall(args: argparse.Namespace) -> None:
    payload = {
        "query": args.query,
        "types": ["world", "experience", "observation"],
        "prefer_observations": True,
        "budget": "mid",
        "max_tokens": args.max_tokens,
        "tags": ["esp32-project", "learning"],
        "tags_match": "all_strict",
        "trace": False,
    }
    print(json.dumps(_request("POST", _bank_path("/memories/recall"), payload), indent=2))


def journey(_: argparse.Namespace) -> None:
    payload = {
        "query": SOURCE_QUERY,
        "budget": "mid",
        "max_tokens": 4096,
        "types": ["world", "experience", "observation"],
        "prefer_observations": True,
        "tags": ["esp32-project", "learning"],
        "tags_match": "all_strict",
        "trace": False,
    }
    result = _request("POST", _bank_path("/memories/recall"), payload)
    print(json.dumps({"mental_model_id": MODEL_ID, **result}, indent=2))


def retain(args: argparse.Namespace) -> None:
    lesson = args.lesson.upper()
    if not re.fullmatch(r"TSK-[A-Z0-9-]+", lesson):
        raise ValueError("lesson must be a TSK lesson code")
    key = re.sub(r"[^a-z0-9-]+", "-", args.key.lower()).strip("-")
    if not key:
        raise ValueError("key must contain letters or numbers")
    document_id = f"esp32-project-{lesson}-{key}"
    payload = {
        "async": False,
        "items": [{
            "content": args.summary,
            "timestamp": datetime.now().astimezone().isoformat(),
            "context": f"ESP32-project learner-help session; verified for {lesson}",
            "document_id": document_id,
            "metadata": {
                "project": "ESP32-S3 learning project",
                "lesson_id": lesson,
                "source": "codex-learner-help",
                "verification": args.verification,
            },
            "tags": [
                "esp32-project", "learning", f"lesson:{lesson}",
                f"memory-shape:{args.shape}",
            ],
            "observation_scopes": "combined",
            "strategy": STRATEGY,
            "update_mode": "replace",
        }],
    }
    result = _request("POST", _bank_path("/memories"), payload)
    print(json.dumps({"document_id": document_id, "result": result}, indent=2))


def status(_: argparse.Namespace) -> None:
    config = _request("GET", _bank_path("/config"))
    model = _request("GET", _bank_path(f"/mental-models/{MODEL_ID}?detail=full"), check=False)
    resolved = config.get("config") or {}
    strategies = resolved.get("retain_strategies") or {}
    output = {
        "strategy": strategies.get(STRATEGY),
        "default_strategy": resolved.get("retain_default_strategy"),
        "mental_model": None if model is None else {
            key: model.get(key) for key in (
                "id", "name", "tags", "max_tokens", "trigger",
                "last_refreshed_at", "is_stale", "content",
            )
        },
    }
    print(json.dumps(output, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ensure").set_defaults(func=ensure)
    sub.add_parser("status").set_defaults(func=status)
    rec = sub.add_parser("recall")
    rec.add_argument("--query", required=True)
    rec.add_argument("--max-tokens", type=int, default=2048)
    rec.set_defaults(func=recall)
    sub.add_parser("journey").set_defaults(func=journey)
    ret = sub.add_parser("retain")
    ret.add_argument("--lesson", required=True)
    ret.add_argument("--key", required=True)
    ret.add_argument("--summary", required=True)
    ret.add_argument("--shape", choices=["concept", "setup", "correction", "incident", "preference"], required=True)
    ret.add_argument("--verification", default="learner-confirmed-and-source-checked")
    ret.set_defaults(func=retain)
    args = parser.parse_args()
    try:
        args.func(args)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

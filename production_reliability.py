"""Persistent production-run status ledger for Nūr Media Production."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_manifest(run_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "running",
        "current_stage": "initialising",
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "stages": [],
        "outputs": {},
        "error": None,
        "manual_review_required": True,
    }


def update_stage(manifest: dict[str, Any], stage: str, status: str,
                 details: str = "") -> dict[str, Any]:
    manifest["current_stage"] = stage
    manifest["updated_at"] = utc_now()
    manifest["stages"].append({
        "stage": stage,
        "status": status,
        "timestamp": manifest["updated_at"],
        "details": details,
    })
    # A completed stage does not mean the entire production run is complete.
    # Overall completion is set by the pipeline only after every stage succeeds.
    if status == "failed":
        manifest["status"] = "failed"
    return manifest


def record_failure(manifest: dict[str, Any], error: BaseException) -> dict[str, Any]:
    manifest["status"] = "failed"
    manifest["updated_at"] = utc_now()
    manifest["error"] = {
        "type": type(error).__name__,
        "message": str(error)[:1000],
    }
    manifest["stages"].append({
        "stage": manifest.get("current_stage", "unknown"),
        "status": "failed",
        "timestamp": manifest["updated_at"],
        "details": f"{type(error).__name__}: {str(error)[:1000]}",
    })
    return manifest


def save_run_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(destination)
    return destination

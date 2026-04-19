#!/usr/bin/env python3
"""Small helpers for pipeline workspace status."""
from __future__ import annotations

import json
from pathlib import Path


def infer_workspace(pdf: Path | None = None, workspace: Path | None = None) -> Path:
    if workspace is not None:
        return workspace
    if pdf is None:
        raise ValueError("pdf or workspace required")
    return pdf.parent / f"{pdf.stem}.ocr"


def status_path(workspace: Path) -> Path:
    internal = workspace / "_internal"
    internal.mkdir(parents=True, exist_ok=True)
    return internal / "_pipeline_status.json"


def write_status(workspace: Path, payload: dict) -> Path:
    target = status_path(workspace)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def read_status(workspace: Path) -> dict:
    target = status_path(workspace)
    if not target.is_file():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}

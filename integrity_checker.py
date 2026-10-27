"""Core functions for a defensive file-integrity checker."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 hex digest for a file, reading it in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_directory(root: Path, excluded_paths: set[Path] | None = None) -> dict[str, dict[str, Any]]:
    """Create a relative-path keyed inventory for regular files under root."""
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Target directory does not exist or is not a directory: {root}")

    excluded = {p.resolve() for p in (excluded_paths or set())}
    inventory: dict[str, dict[str, Any]] = {}

    for path in sorted(root.rglob("*")):
        # Do not follow symlinks; they can point outside the chosen evidence folder.
        if path.is_symlink() or not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in excluded:
            continue
        stat = path.stat()
        inventory[path.relative_to(root).as_posix()] = {
            "sha256": sha256_file(path),
            "size_bytes": stat.st_size,
            "modified_utc": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
        }
    return inventory


def create_baseline(root: Path, baseline_path: Path) -> dict[str, Any]:
    """Inventory root and save a JSON baseline outside the scanned tree when possible."""
    baseline_path = baseline_path.resolve()
    inventory = inventory_directory(root, {baseline_path})
    document = {
        "schema_version": 1,
        "algorithm": "SHA-256",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root_label": root.resolve().name,
        "files": inventory,
    }
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return document


def load_baseline(path: Path) -> dict[str, Any]:
    """Load and validate a baseline JSON document."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Baseline not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Baseline is not valid JSON: {path}") from exc

    if document.get("schema_version") != 1 or not isinstance(document.get("files"), dict):
        raise ValueError("Unsupported or malformed baseline format.")
    for relative_path, record in document["files"].items():
        if not isinstance(relative_path, str) or not isinstance(record, dict):
            raise ValueError("Malformed file entry in baseline.")
        if not isinstance(record.get("sha256"), str):
            raise ValueError(f"Missing SHA-256 value for {relative_path}")
    return document


def compare_inventory(
    baseline_files: dict[str, dict[str, Any]],
    current_files: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    """Compare inventories and return added, modified, and missing relative paths."""
    baseline_names = set(baseline_files)
    current_names = set(current_files)
    added = sorted(current_names - baseline_names)
    missing = sorted(baseline_names - current_names)
    modified = sorted(
        name for name in baseline_names & current_names
        if baseline_files[name].get("sha256") != current_files[name].get("sha256")
    )
    return {"added": added, "modified": modified, "missing": missing}


def verify_directory(root: Path, baseline_path: Path) -> dict[str, Any]:
    """Compare a directory against a saved baseline."""
    baseline_path = baseline_path.resolve()
    baseline = load_baseline(baseline_path)
    current = inventory_directory(root, {baseline_path})
    changes = compare_inventory(baseline["files"], current)
    return {
        "schema_version": 1,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "root_label": root.resolve().name,
        "status": "CLEAN" if not any(changes.values()) else "CHANGES DETECTED",
        "checked_files": len(current),
        "added": changes["added"],
        "modified": changes["modified"],
        "missing": changes["missing"],
    }

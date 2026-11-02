"""Deterministic SHA-256 canonical fingerprint generation."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

FINGERPRINT_ALGORITHM_VERSION = "1.0.0"

# Canonical type mappings
DATA_TYPE_NORMALIZATIONS = {
    "int": "INTEGER",
    "integer": "INTEGER",
    "int32": "INTEGER",
    "int64": "BIGINT",
    "bigint": "BIGINT",
    "smallint": "SMALLINT",
    "tinyint": "TINYINT",
    "varchar": "STRING",
    "nvarchar": "STRING",
    "string": "STRING",
    "text": "STRING",
    "char": "STRING",
    "nchar": "STRING",
    "bool": "BOOLEAN",
    "boolean": "BOOLEAN",
    "bit": "BOOLEAN",
    "float": "DOUBLE",
    "float64": "DOUBLE",
    "double": "DOUBLE",
    "real": "FLOAT",
    "datetime": "TIMESTAMP",
    "datetime2": "TIMESTAMP",
    "timestamp": "TIMESTAMP",
    "date": "DATE",
    "decimal": "DECIMAL",
    "numeric": "DECIMAL",
    "binary": "BINARY",
    "varbinary": "BINARY",
}


def normalize_data_type(source_type: str | None) -> str:
    """Normalizes raw SQL or engine types into canonical types."""
    if not source_type:
        return "UNKNOWN"
    base = source_type.strip().lower().split("(")[0].strip()
    return DATA_TYPE_NORMALIZATIONS.get(base, base.upper())


def _canonicalize_value(val: Any) -> Any:
    """Recursively formats structures into canonical sorted representations."""
    if val is None:
        return None
    if isinstance(val, bool):
        return bool(val)
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, (list, tuple, set)):
        # If it's a sequence of primitives or dicts
        items = [_canonicalize_value(x) for x in val]
        # Only sort if elements are directly comparable strings/ints
        if all(isinstance(x, (str, int, float)) for x in items):
            return sorted(items)
        return items
    if isinstance(val, dict):
        return {k: _canonicalize_value(val[k]) for k in sorted(val.keys())}
    return str(val)


def canonicalize(data: dict[str, Any], exclude_keys: Sequence[str] = ()) -> str:
    """Produces a deterministic canonical JSON string."""
    filtered = {
        k: _canonicalize_value(v)
        for k, v in sorted(data.items())
        if k not in exclude_keys and not k.startswith("_")
    }
    return json.dumps(filtered, separators=(",", ":"), ensure_ascii=True, sort_keys=True)


def compute_fingerprint(data: dict[str, Any], exclude_keys: Sequence[str] = ()) -> str:
    """Calculates SHA-256 hash of canonical JSON."""
    c_json = canonicalize(data, exclude_keys)
    return hashlib.sha256(c_json.encode("utf-8")).hexdigest()


def compute_column_fingerprint(
    table_id: str,
    column_name: str,
    data_type: str,
    source_data_type: str | None = None,
    nullable: bool | None = None,
    ordinal_position: int | None = None,
    description: str | None = None,
) -> str:
    """Computes stable column fingerprint."""
    payload = {
        "table_id": table_id,
        "column_name": column_name.lower().strip(),
        "data_type": normalize_data_type(data_type),
        "source_data_type": source_data_type.strip() if source_data_type else None,
        "nullable": nullable,
        "ordinal_position": ordinal_position,
        "description": description.strip() if description else None,
        "algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
    }
    return compute_fingerprint(payload)


def compute_table_fingerprint(
    lakehouse_id: str,
    schema_name: str | None,
    table_name: str,
    table_format: str,
    column_fingerprints: Sequence[str],
    description: str | None = None,
) -> str:
    """Computes stable table fingerprint including its ordered or sorted column fingerprints."""
    payload = {
        "lakehouse_id": lakehouse_id,
        "schema_name": (schema_name or "dbo").lower().strip(),
        "table_name": table_name.lower().strip(),
        "table_format": table_format.upper().strip(),
        "column_fingerprints": sorted(column_fingerprints),
        "description": description.strip() if description else None,
        "algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
    }
    return compute_fingerprint(payload)


def compute_edge_fingerprint(
    source_node_id: str,
    target_node_id: str,
    edge_type: str,
    evidence_type: str,
    evidence_ref: str | None = None,
) -> str:
    """Computes edge fingerprint."""
    payload = {
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "edge_type": edge_type,
        "evidence_type": evidence_type,
        "evidence_ref": evidence_ref,
        "algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
    }
    return compute_fingerprint(payload)

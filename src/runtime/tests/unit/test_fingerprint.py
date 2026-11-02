"""Unit tests for canonical fingerprinting."""

from __future__ import annotations

from lakehouse_intelligence.graph.fingerprint import (
    canonicalize,
    compute_column_fingerprint,
    compute_fingerprint,
    compute_table_fingerprint,
    normalize_data_type,
)


def test_canonicalize_sorts_keys():
    d1 = {"b": 2, "a": 1, "c": [3, 2, 1]}
    d2 = {"a": 1, "c": [1, 2, 3], "b": 2}
    assert canonicalize(d1) == canonicalize(d2)


def test_compute_fingerprint_deterministic():
    d = {"name": "customers", "schema": "dbo", "format": "DELTA"}
    fp1 = compute_fingerprint(d)
    fp2 = compute_fingerprint(d)
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex string


def test_normalize_data_type():
    assert normalize_data_type("varchar(255)") == "STRING"
    assert normalize_data_type("int") == "INTEGER"
    assert normalize_data_type("bigint") == "BIGINT"
    assert normalize_data_type("boolean") == "BOOLEAN"
    assert normalize_data_type("timestamp") == "TIMESTAMP"


def test_column_fingerprint_stability():
    fp1 = compute_column_fingerprint(
        table_id="tbl1",
        column_name="customer_id",
        data_type="varchar",
        nullable=False,
    )
    fp2 = compute_column_fingerprint(
        table_id="tbl1",
        column_name="CUSTOMER_ID",
        data_type="STRING",
        nullable=False,
    )
    assert fp1 == fp2


def test_table_fingerprint_changes_on_column_change():
    col_fps_1 = ["fp1", "fp2"]
    col_fps_2 = ["fp1", "fp3"]
    t1 = compute_table_fingerprint("lh1", "dbo", "customers", "DELTA", col_fps_1)
    t2 = compute_table_fingerprint("lh1", "dbo", "customers", "DELTA", col_fps_2)
    assert t1 != t2


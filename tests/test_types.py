"""Tests for validation helpers and error types."""

from __future__ import annotations

import pytest

from memcp.types import (
    canonical_error,
    reject_nested_filters,
    validate_memory_id,
)

# ---------------------------------------------------------------------------
# validate_memory_id
# ---------------------------------------------------------------------------


class TestValidateMemoryId:
    def test_valid_uuid(self):
        assert validate_memory_id("abc-123-def") == "abc-123-def"

    def test_valid_alphanumeric(self):
        assert validate_memory_id("memory_42") == "memory_42"

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError, match="Invalid memory_id"):
            validate_memory_id("")

    def test_too_long_rejected(self):
        with pytest.raises(ValueError, match="Invalid memory_id"):
            validate_memory_id("a" * 129)

    def test_max_length_accepted(self):
        assert validate_memory_id("a" * 128) == "a" * 128

    def test_special_chars_rejected(self):
        with pytest.raises(ValueError, match="Invalid memory_id"):
            validate_memory_id("memory id with spaces")

    def test_path_traversal_rejected(self):
        with pytest.raises(ValueError, match="Invalid memory_id"):
            validate_memory_id("../../etc/passwd")

    def test_url_injection_rejected(self):
        with pytest.raises(ValueError, match="Invalid memory_id"):
            validate_memory_id("id?user_id=attacker")


# ---------------------------------------------------------------------------
# reject_nested_filters
# ---------------------------------------------------------------------------


class TestRejectNestedFilters:
    def test_flat_filters_pass(self):
        reject_nested_filters({"agent_id": "a1", "run_id": "r1"})

    def test_and_rejected(self):
        with pytest.raises(ValueError, match="Nested boolean"):
            reject_nested_filters({"AND": [{"agent_id": "a1"}]})

    def test_or_rejected(self):
        with pytest.raises(ValueError, match="Nested boolean"):
            reject_nested_filters({"OR": [{"a": 1}, {"b": 2}]})

    def test_not_rejected(self):
        with pytest.raises(ValueError, match="Nested boolean"):
            reject_nested_filters({"NOT": {"agent_id": "a1"}})

    def test_case_insensitive(self):
        with pytest.raises(ValueError, match="Nested boolean"):
            reject_nested_filters({"and": [{"a": 1}]})

    def test_empty_dict_passes(self):
        reject_nested_filters({})


# ---------------------------------------------------------------------------
# canonical_error
# ---------------------------------------------------------------------------


class TestCanonicalError:
    def test_structure(self):
        err = canonical_error("not_found", "Memory not found")
        assert err == {
            "error": {"code": "not_found", "message": "Memory not found", "retry": False}
        }

    def test_retry_flag(self):
        err = canonical_error("timeout", "Backend timeout", retry=True)
        assert err["error"]["retry"] is True

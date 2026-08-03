"""Proves the qrf package imports and the test suite runs."""

import qrf
import qrf.kernel
from qrf.errors import IntegrityViolation, QRFError, SchemaViolation


def test_package_imports():
    assert qrf is not None
    assert qrf.kernel is not None


def test_error_hierarchy():
    assert issubclass(SchemaViolation, QRFError)
    assert issubclass(IntegrityViolation, QRFError)


def test_errors_carry_what_and_value():
    err = SchemaViolation("field_type", 42)
    assert err.what == "field_type"
    assert err.value == 42
    assert "field_type" in str(err)

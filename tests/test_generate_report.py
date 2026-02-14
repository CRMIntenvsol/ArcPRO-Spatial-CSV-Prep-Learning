import pytest
from generate_report import clean_value

def test_clean_value_basic():
    """Test basic stripping and lowercasing."""
    assert clean_value("  Hello World  ") == "hello world"
    assert clean_value("PYTHON") == "python"

def test_clean_value_empty_and_none():
    """Test handling of None and empty strings."""
    assert clean_value("") == ""
    assert clean_value(None) == ""

def test_clean_value_falsy_inputs():
    """Test handling of other falsy Python values."""
    # Current implementation 'if not val: return ""' means these should return ""
    assert clean_value(0) == ""
    assert clean_value(False) == ""
    assert clean_value([]) == ""
    assert clean_value({}) == ""

def test_clean_value_whitespace():
    """Test various whitespace characters."""
    assert clean_value("\n  test\t") == "test"
    assert clean_value("   ") == ""

def test_clean_value_non_string_truthy():
    """Test truthy non-string inputs which should raise AttributeError."""
    with pytest.raises(AttributeError):
        clean_value(123)
    with pytest.raises(AttributeError):
        clean_value([1, 2, 3])

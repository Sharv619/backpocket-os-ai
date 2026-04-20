"""Tests for ABN checksum validator."""
import pytest
from services.abn_validator import validate_abn, format_abn, validate_gst_amount, abn_info


# ── Known valid ABNs (from ATO examples) ──────────────────────────────────────
VALID_ABNS = [
    "51824753556",   # ATO example
    "51 824 753 556",  # with spaces
    "53004085616",   # Woolworths Group
    "49004028077",   # BHP Group
]

INVALID_ABNS = [
    "12345678901",   # bad checksum
    "00000000000",   # all zeros
    "1234",          # too short
    "123456789012",  # too long
    "5182475355X",   # non-digit
    "",              # empty
]


class TestValidateAbn:
    def test_valid_abns_pass(self):
        for abn in VALID_ABNS:
            assert validate_abn(abn), f"Expected {abn!r} to be valid"

    def test_invalid_abns_fail(self):
        for abn in INVALID_ABNS:
            assert not validate_abn(abn), f"Expected {abn!r} to be invalid"

    def test_strips_spaces(self):
        assert validate_abn("51 824 753 556") == validate_abn("51824753556")

    def test_strips_hyphens(self):
        assert validate_abn("51-824-753-556") == validate_abn("51824753556")

    def test_non_string_digits_fail(self):
        assert not validate_abn("ABCDEFGHIJK")


class TestFormatAbn:
    def test_formats_valid_abn(self):
        assert format_abn("51824753556") == "51 824 753 556"

    def test_formats_spaced_abn(self):
        assert format_abn("51 824 753 556") == "51 824 753 556"

    def test_returns_original_on_wrong_length(self):
        assert format_abn("1234") == "1234"


class TestValidateGst:
    def test_correct_gst(self):
        assert validate_gst_amount(10000, 1000)   # $100.00 subtotal, $10.00 GST

    def test_incorrect_gst(self):
        assert not validate_gst_amount(10000, 1500)  # $15 GST on $100 is wrong

    def test_rounding_tolerance(self):
        # $33.33 * 0.1 = $3.333 → rounds to $3 or $4
        assert validate_gst_amount(3333, 333) or validate_gst_amount(3333, 334)

    def test_zero_subtotal(self):
        assert validate_gst_amount(0, 0)


class TestAbnInfo:
    def test_valid_abn_returns_formatted(self):
        result = abn_info("51824753556")
        assert result["valid"] is True
        assert result["formatted"] == "51 824 753 556"
        assert result["error"] is None

    def test_invalid_abn_returns_error(self):
        result = abn_info("12345678901")
        assert result["valid"] is False
        assert result["formatted"] is None
        assert "checksum" in result["error"].lower()

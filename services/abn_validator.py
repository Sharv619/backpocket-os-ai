"""Australian Business Number (ABN) validation — ATO checksum algorithm."""
import re

# ATO weighting factors (position 1-11)
_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]


def _normalise(abn: str) -> str:
    return re.sub(r"[\s\-]", "", abn)


def validate_abn(abn: str) -> bool:
    """
    Validate an ABN using the ATO checksum algorithm.
    Ref: https://abr.business.gov.au/Help/AbnFormat
    """
    digits = _normalise(abn)
    if not digits.isdigit() or len(digits) != 11:
        return False
    nums = [int(d) for d in digits]
    nums[0] -= 1  # subtract 1 from first digit
    total = sum(w * d for w, d in zip(_WEIGHTS, nums))
    return total % 89 == 0


def format_abn(abn: str) -> str:
    """Return ABN in display format: XX XXX XXX XXX."""
    digits = _normalise(abn)
    if len(digits) != 11:
        return abn
    return f"{digits[:2]} {digits[2:5]} {digits[5:8]} {digits[8:11]}"


def validate_gst_amount(subtotal_cents: int, gst_cents: int) -> bool:
    """Assert GST is exactly 10% of subtotal (within 1 cent rounding tolerance)."""
    expected = round(subtotal_cents * 0.1)
    return abs(gst_cents - expected) <= 1


def abn_info(abn: str) -> dict:
    """Return structured ABN info dict."""
    digits = _normalise(abn)
    is_valid = validate_abn(abn)
    return {
        "abn": digits,
        "formatted": format_abn(abn) if is_valid else None,
        "valid": is_valid,
        "error": None if is_valid else "Invalid ABN — checksum failed",
    }

# tests/test_vcard.py
from pathlib import Path

VCF = Path(__file__).resolve().parents[1] / "site" / "dhruv.vcf"


def test_uses_vcard_3_for_ios_compatibility():
    assert "VERSION:3.0" in VCF.read_text()


def test_required_identity_fields():
    t = VCF.read_text()
    assert "FN:Dhruv Bangera" in t
    assert "N:Bangera;Dhruv;;;" in t
    assert "TITLE:AI Engineer" in t
    assert "ORG:Parker Technology" in t


def test_email_present():
    assert "dhruv.bangera@parkertechnology.com" in VCF.read_text()


def test_linkedin_uses_single_b():
    """Regression guard. Dhruv corrected dhruvbbangera -> dhruvbangera on 2026-09-14.
    LinkedIn returns 999 for both spellings, so no automated check can catch this —
    only this assertion can."""
    t = VCF.read_text()
    assert "linkedin.com/in/dhruvbangera" in t
    assert "dhruvbbangera" not in t, "double-b typo has regressed"


def test_no_phone_number_anywhere():
    """Explicit product decision: no phone. A QR in the wild cannot be retracted."""
    assert "TEL" not in VCF.read_text()


def test_crlf_line_endings():
    """RFC 6350 requires CRLF. Some iOS versions reject LF-only vCards."""
    assert b"\r\n" in VCF.read_bytes()

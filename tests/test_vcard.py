# tests/test_vcard.py
from pathlib import Path

VCF = Path(__file__).resolve().parents[1] / "site" / "dhruv.vcf"


def unfolded() -> str:
    """The vCard as a consumer sees it.

    RFC 6350 folds long lines as CRLF + a single space, and readers rejoin them
    before interpreting. Asserting against the raw bytes tests the wire format,
    not the content — and silently breaks once a value crosses 75 octets.
    """
    return VCF.read_bytes().decode().replace("\r\n ", "")


def properties() -> list[str]:
    """Unfolded property lines, so a substring can't be matched inside base64."""
    return [l for l in unfolded().split("\r\n") if l]


def test_uses_vcard_3_for_ios_compatibility():
    assert "VERSION:3.0" in properties()


def test_required_identity_fields():
    p = properties()
    assert "FN:Dhruv Bangera" in p
    assert "N:Bangera;Dhruv;;;" in p
    assert "TITLE:AI Engineer" in p
    assert "ORG:Parker Technology" in p


def test_email_present():
    assert any(
        l.startswith("EMAIL") and l.endswith("dhruv.bangera@parkertechnology.com")
        for l in properties()
    )


def test_linkedin_uses_single_b():
    """Regression guard. Dhruv corrected dhruvbbangera -> dhruvbangera on 2026-09-14.
    LinkedIn returns 999 for both spellings, so no network check can catch this —
    only this assertion can.

    Must read the UNFOLDED card: folding splits this URL mid-string, which made an
    earlier version of this test silently stop matching.
    """
    t = unfolded()
    assert "linkedin.com/in/dhruvbangera" in t
    assert "dhruvbbangera" not in t, "double-b typo has regressed"


def test_no_phone_number_anywhere():
    """Explicit product decision: no phone. A QR in the wild cannot be retracted.

    Checks property NAMES, not raw text — 'TEL' can occur by chance inside the
    base64 photo, which would fail this test for an entirely unrelated reason.
    """
    offenders = [l for l in properties() if l.upper().startswith("TEL")]
    assert not offenders, f"phone number present: {offenders}"


def test_crlf_line_endings():
    """RFC 6350 requires CRLF. Some iOS versions reject LF-only vCards.
    Checks no BARE LF exists — `b"\\r\\n" in data` would pass on one CRLF + nine LFs."""
    data = VCF.read_bytes()
    assert data.replace(b"\r\n", b"").count(b"\n") == 0, "bare LF found"


def test_photo_embedded_as_base64_png():
    """Parker mark appears as the contact photo in iOS Contacts."""
    assert any(l.startswith("PHOTO;ENCODING=b;TYPE=PNG:") for l in properties())


def test_photo_folded_to_75_octets():
    """RFC 6350: lines over 75 octets must be folded with CRLF + single space,
    or Apple Contacts truncates the photo. Checks EVERY raw line, not just PHOTO —
    X-SOCIALPROFILE is 90 octets unfolded."""
    for raw in VCF.read_bytes().split(b"\r\n"):
        assert len(raw) <= 75, f"unfolded line of {len(raw)} octets"


def test_photo_decodes_to_a_real_png():
    """The photo must be a valid PNG, not truncated base64.
    Folding bugs corrupt this in a way every string assertion above would miss."""
    import base64

    line = next(l for l in properties() if l.startswith("PHOTO;"))
    blob = base64.b64decode(line.split(":", 1)[1], validate=True)
    assert blob[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    assert len(blob) > 500, f"suspiciously small: {len(blob)} bytes"

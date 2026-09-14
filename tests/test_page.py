# tests/test_page.py
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "site" / "index.html"


def test_has_mailto_link():
    assert "mailto:dhruv.bangera@parkertechnology.com" in HTML.read_text()


def test_has_linkedin_link_single_b():
    t = HTML.read_text()
    assert "https://www.linkedin.com/in/dhruvbangera" in t
    assert "dhruvbbangera" not in t


def test_has_vcard_download():
    assert 'href="dhruv.vcf"' in HTML.read_text()


def test_no_phone_number():
    t = HTML.read_text()
    assert "tel:" not in t


def test_declares_apple_web_app_meta():
    """Required for Add to Home Screen to open without Safari chrome."""
    t = HTML.read_text()
    assert "apple-mobile-web-app-capable" in t
    assert "apple-touch-icon" in t


def test_identity_matches_spec():
    t = HTML.read_text()
    for s in ("Dhruv Bangera", "AI Engineer", "Parker Technology"):
        assert s in t

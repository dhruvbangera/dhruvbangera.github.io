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


def _dark_block() -> str:
    """The body of the prefers-color-scheme: dark media query, by brace matching."""
    t = HTML.read_text()
    i = t.index("prefers-color-scheme: dark")
    i = t.index("{", i)
    depth, j = 0, i
    while j < len(t):
        if t[j] == "{":
            depth += 1
        elif t[j] == "}":
            depth -= 1
            if depth == 0:
                return t[i:j + 1]
        j += 1
    raise AssertionError("unterminated dark media query")


def test_dark_mode_styles_the_bold_hint_text():
    """Regression guard: the Add-to-Home-Screen hint is the only text outside the
    white sheet. The dark block recoloured `.hint` but not `.hint b`, so the two
    bolded words rendered #0b0b0c on #000 — about 1.07:1 contrast, i.e. the sentence
    read "tap [blank], then [blank]". Reported from a real device.
    """
    dark = _dark_block()
    assert ".hint b" in dark, "dark mode must recolour .hint b or it vanishes on black"
    assert "#0b0b0c" not in dark, "near-black in the dark block is the original bug"

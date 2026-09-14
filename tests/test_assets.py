# tests/test_assets.py
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site" / "assets"
URL = "https://dhruvbangera.github.io"


def build():
    subprocess.run([sys.executable, str(ROOT / "build/build.py")],
                   check=True, cwd=ROOT)


build()


def test_wordmark_recolored_for_white_background():
    svg = (ASSETS / "parker-wordmark.svg").read_text()
    assert "#025172" in svg, "wordmark must use Parker deep teal"


def test_wordmark_preserves_accent_colors():
    svg = (ASSETS / "parker-wordmark.svg").read_text()
    assert "#6697a9" in svg, "slate accent must survive recolor"
    assert "#e3d71d" in svg, "yellow accent must survive recolor"


def test_square_mark_is_untouched_and_square():
    svg = (ASSETS / "parker-mark.svg").read_text()
    assert 'viewBox="0 0 500 500"' in svg, "mark must stay square for circular contact-photo crop"
    assert "#025172" in svg


def test_qr_decodes_to_exact_url():
    """The single most important test in this repo.
    A QR that scans to the wrong place is worse than no QR."""
    import cv2
    png = ASSETS / "qr-check.png"
    got, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(str(png)))
    assert got == URL, f"QR decoded to {got!r}, expected {URL!r}"

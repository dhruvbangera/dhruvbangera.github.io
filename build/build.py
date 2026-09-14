# build/build.py
"""Generate all brand assets. Idempotent; safe to re-run."""
import urllib.request
from pathlib import Path
import segno

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "site" / "assets"
URL = "https://dhruvbangera.github.io"

WORDMARK_SRC = "https://parkertechnology.com/media/parker-technology-logo-reversed.svg"
MARK_SRC = "https://parkertechnology.com/media/parker-technology-site-icon.svg"

PT_TEAL = "#025172"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    # Wordmark: published reversed (white). Recolor white -> Parker teal for a white card.
    # Accents #6697a9 and #e3d71d are intentionally left alone.
    wordmark = fetch(WORDMARK_SRC).replace("fill:#fff;", f"fill:{PT_TEAL};")
    assert "fill:#fff" not in wordmark.replace(" ", ""), "recolor failed; upstream SVG changed"
    (ASSETS / "parker-wordmark.svg").write_text(wordmark)

    # Square mark: already light-background colors. Used for apple-touch-icon + vCard PHOTO.
    (ASSETS / "parker-mark.svg").write_text(fetch(MARK_SRC))

    # QR, error correction H for glare/screen margin.
    qr = segno.make(URL, error="h")
    qr.save(ASSETS / "qr.svg", kind="svg", scale=10, dark=PT_TEAL, light=None, border=0)
    # PNG twin exists purely so tests can decode it.
    qr.save(ASSETS / "qr-check.png", scale=10, dark=PT_TEAL, light="#ffffff", border=3)

    print(f"assets written to {ASSETS}")


if __name__ == "__main__":
    main()

# Digital Business Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a zero-cost, fully-native digital business card — one Action Button press shows it offline on Dhruv's iPhone, and its QR gives anyone a keepable contact card.

**Architecture:** The card is a single HTML/CSS component. `index.html` renders it live on GitHub Pages for recipients; the Playwright MCP screenshots that same component to produce the offline image Dhruv shows. Two halves share only the URL string, so neither can drift from the other.

**Tech Stack:** Static HTML/CSS (no framework), `segno` (QR), `opencv-python-headless` (QR decode verification), `pytest`, Playwright MCP (rendering), GitHub Pages (hosting), Apple Shortcuts (trigger).

**Spec:** `docs/superpowers/specs/2026-09-14-digital-business-card-design.md`

---

## Verified facts (do not re-litigate)

These were established with commands, not assumptions:

| Fact | Evidence |
|---|---|
| No Apple signing identity exists | `security find-identity -v -p codesigning` → 0 valid identities |
| Action Button **can** run a Shortcut | Apple Shortcuts User Guide |
| Camera Control **cannot** run arbitrary Shortcuts | Apple only exposes "which camera app"; workaround visibly launches another app |
| GitHub is the only authenticated host | `gh auth status` OK; `vercel whoami` no credentials; `render` → 401 |
| QR in `#025172` decodes correctly | segno + `cv2.QRCodeDetector` → exact match at scale 6 and 10, ECC H |
| No SVG rasterizer installed | `rsvg-convert`/`inkscape`/`magick`/`cairosvg`/`resvg` all absent |
| No standalone Playwright chromium | only `mcp-chrome-*` in the cache → use the MCP, do not `npx playwright install` |
| Parker publishes only a reversed logo | all standard-variant paths 404 |

## Contact data (single source — copy exactly)

```
Name      Dhruv Bangera
Title     AI Engineer
Company   Parker Technology
Email     dhruv.bangera@parkertechnology.com
LinkedIn  https://www.linkedin.com/in/dhruvbangera     ← SINGLE b. Corrected from dhruvbbangera.
URL       https://dhruvbangera.github.io
Phone     OMITTED BY DECISION — do not add one.
```

## File structure

| File | Responsibility |
|---|---|
| `build/requirements.txt` | pinned build deps |
| `build/build.py` | fetch + recolor logo, generate QR — the only asset generator |
| `build/verify.py` | decode the QR out of a rendered PNG |
| `tests/test_assets.py` | logo recolor + QR decode |
| `tests/test_vcard.py` | vCard correctness, incl. the no-phone and single-b guards |
| `tests/test_page.py` | required links present in the page |
| `site/card.css` | the one shared card component |
| `site/index.html` | recipient page: card + 3 actions |
| `site/dhruv.vcf` | vCard 3.0 |
| `site/assets/*` | generated — mark, wordmark, qr, icon |
| `site/manifest.webmanifest` | Add to Home Screen |
| `site/pass.json` | unsigned, parked |
| `SHORTCUT.md` | iPhone setup + the on-device checklist |
| `CLAUDE.md` | constraints for future sessions |

---

## Task 1: Scaffold the build environment

**Files:**
- Create: `build/requirements.txt`, `.gitignore` (modify)

- [ ] **Step 1: Pin dependencies**

```bash
cd /Users/dhruvbangera/Desktop/Digital_Business_Card
mkdir -p build tests site/assets
cat > build/requirements.txt <<'EOF'
segno==1.6.6
opencv-python-headless==5.0.0.88
pytest==9.1.1
EOF
```

- [ ] **Step 2: Create the venv and install**

```bash
python3 -m venv build/.venv
build/.venv/bin/pip -q install -r build/requirements.txt
build/.venv/bin/python -c "import segno,cv2,pytest;print('ok',segno.__version__,cv2.__version__)"
```

Expected: `ok 1.6.6 5.0.0`

If `opencv-python-headless==5.0.0.88` fails to resolve, relax to `opencv-python-headless>=4.10` — the only API used is `cv2.QRCodeDetector`, stable across both.

- [ ] **Step 3: Ignore the venv**

```bash
printf 'build/.venv/\nout/\n.DS_Store\n__pycache__/\n.pytest_cache/\nnode_modules/\n' > .gitignore
```

- [ ] **Step 4: Commit**

```bash
git add build/requirements.txt .gitignore
git commit -m "build: pin QR + verification toolchain"
```

---

## Task 2: Brand assets — recolor the logo, generate the QR

Parker publishes only a **reversed** (white-on-dark) wordmark. The card is white, so the
white fill must become `#025172`. The square site icon needs no recolor.

**Files:**
- Create: `build/build.py`, `tests/test_assets.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_assets.py
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site" / "assets"
URL = "https://dhruvbangera.github.io"


def build():
    subprocess.run([sys.executable, str(ROOT / "build/build.py")], check=True, cwd=ROOT)


# Build ONCE for the module. Calling it per-test made 8 HTTP requests per run and
# made the QR test fail with a urllib traceback whenever Parker's CDN was down —
# even though the QR assertion needs nothing but local segno.
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
```

- [ ] **Step 2: Run it and watch it fail**

```bash
build/.venv/bin/python -m pytest tests/test_assets.py -v
```

Expected: FAIL — `build/build.py` does not exist.

- [ ] **Step 3: Write the generator**

```python
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
    # Positive check: asserting the ABSENCE of the old value after replacing it
    # cannot tell "replaced" from "that spelling was never there" — so a Parker
    # change to fill:#FFF; or fill:white; would silently ship a white-on-white logo.
    src = fetch(WORDMARK_SRC)
    assert src.count("fill:#fff;") == 1, "recolor failed; upstream SVG changed"
    wordmark = src.replace("fill:#fff;", f"fill:{PT_TEAL};")
    (ASSETS / "parker-wordmark.svg").write_text(wordmark)

    # Square mark: already light-background colors. Used for apple-touch-icon + vCard PHOTO.
    (ASSETS / "parker-mark.svg").write_text(fetch(MARK_SRC))

    # QR, error correction H for glare/screen margin.
    # border=4 is the spec-required quiet zone. VERIFIED: border=0 does not decode
    # at all. Shared opts so the shipped SVG and the tested PNG cannot drift in the
    # one dimension that decides whether the thing scans.
    qr = segno.make(URL, error="h")
    qr_opts = dict(scale=10, dark=PT_TEAL, border=4)
    qr.save(ASSETS / "qr.svg", kind="svg", light=None, **qr_opts)
    # PNG twin exists purely so tests can decode it.
    qr.save(ASSETS / "qr-check.png", light="#ffffff", **qr_opts)

    print(f"assets written to {ASSETS}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and watch them pass**

```bash
build/.venv/bin/python -m pytest tests/test_assets.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add build/build.py tests/test_assets.py site/assets
git commit -m "feat: brand assets — recolored wordmark + brand-teal QR

QR decode verified against the exact URL; ECC level H for screen glare."
```

---

## Task 3: vCard

`text/vcard` handed to Safari opens the **native iOS Add Contact sheet**. vCard 3.0, not 4.0 —
3.0 is what Apple Contacts imports most reliably.

**Files:**
- Create: `site/dhruv.vcf`, `tests/test_vcard.py`

- [ ] **Step 1: Write the failing test**

```python
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
    """RFC 6350 requires CRLF. Some iOS versions reject LF-only vCards.
    Checks no BARE LF exists — `b"\r\n" in data` would pass on one CRLF + nine LFs."""
    data = VCF.read_bytes()
    assert data.replace(b"\r\n", b"").count(b"\n") == 0, "bare LF found"
```

- [ ] **Step 2: Run it and watch it fail**

```bash
build/.venv/bin/python -m pytest tests/test_vcard.py -v
```

Expected: FAIL — `site/dhruv.vcf` does not exist.

- [ ] **Step 3: Write the vCard with CRLF endings**

```bash
python3 - <<'PY'
from pathlib import Path
lines = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    "N:Bangera;Dhruv;;;",
    "FN:Dhruv Bangera",
    "ORG:Parker Technology",
    "TITLE:AI Engineer",
    "EMAIL;type=INTERNET;type=WORK;type=pref:dhruv.bangera@parkertechnology.com",
    "URL;type=WORK:https://dhruvbangera.github.io",
    "X-SOCIALPROFILE;type=linkedin;x-user=dhruvbangera:https://www.linkedin.com/in/dhruvbangera",
    "END:VCARD",
]
Path("site/dhruv.vcf").write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
print("wrote site/dhruv.vcf")
PY
```

- [ ] **Step 4: Run the tests and watch them pass**

```bash
build/.venv/bin/python -m pytest tests/test_vcard.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add site/dhruv.vcf tests/test_vcard.py
git commit -m "feat: vCard 3.0 for native iOS Contacts handoff

CRLF per RFC 6350. No TEL by decision. Includes a regression guard on the
LinkedIn single-b correction, which no network check can catch (LinkedIn
returns 999 for any spelling)."
```

---

## Task 4: The card component

One component, two contexts. Sized in `rem` off a root font-size so the screenshot
task can scale it to exact pixels without a second stylesheet.

**Files:**
- Create: `site/card.css`

- [ ] **Step 1: Write the stylesheet**

```css
/* site/card.css — the single card component.
   Rendered live on the page AND screenshotted for the offline image.
   Never fork this file; both contexts must stay identical by construction. */

:root {
  --pt-teal: #025172;
  --pt-slate: #6697a9;
  --pt-yellow: #e3d71d;
  --ink: #0b0b0c;
  --muted: #5c6970;
  --hairline: #e6e8ea;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: #f2f3f5;
  /* -apple-system resolves to the real SF Pro on Apple devices. */
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.card {
  background: #fff;
  width: 100%;
  max-width: 24rem;
  margin: 0 auto;
  padding: 2.75rem 2rem 2.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2rem;
}

.card__wordmark { width: 9.5rem; height: auto; display: block; }

/* Traditional business-card hierarchy: name, then title, then company. */
.card__identity { display: flex; flex-direction: column; gap: 0.3rem; }

.card__name {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--ink);
  line-height: 1.15;
}

.card__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--pt-teal);
  letter-spacing: 0.01em;
}

.card__company {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 400;
  color: var(--muted);
}

.card__qr { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }
.card__qr img { width: 10rem; height: 10rem; display: block; }

.card__scan {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}

/* Full-bleed variant used only by the screenshot task. */
.shot body { background: #fff; }
.shot .card { max-width: none; min-height: 100vh; justify-content: center; gap: 2.5rem; }
```

- [ ] **Step 2: Commit**

```bash
git add site/card.css
git commit -m "feat: card component — traditional name/title/company hierarchy"
```

---

## Task 5: The recipient page

**Files:**
- Create: `site/index.html`, `site/manifest.webmanifest`, `tests/test_page.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run it and watch it fail**

```bash
build/.venv/bin/python -m pytest tests/test_page.py -v
```

Expected: FAIL — `site/index.html` does not exist.

- [ ] **Step 3: Write the page**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Dhruv Bangera — AI Engineer, Parker Technology</title>
<meta name="description" content="Dhruv Bangera, AI Engineer at Parker Technology.">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Dhruv Bangera">
<meta name="theme-color" content="#ffffff">
<link rel="apple-touch-icon" href="assets/icon-180.png">
<link rel="manifest" href="manifest.webmanifest">
<link rel="stylesheet" href="card.css">
<style>
  .wrap { max-width: 24rem; margin: 0 auto; padding: 1.5rem 1rem 3rem; }
  .sheet { background:#fff; border-radius:1.25rem; overflow:hidden;
           box-shadow:0 1px 2px rgba(11,12,12,.06), 0 12px 32px rgba(11,12,12,.08); }
  .actions { border-top:1px solid var(--hairline); }
  .action { display:flex; align-items:center; gap:.875rem; padding:1rem 1.25rem;
            border-bottom:1px solid var(--hairline); text-decoration:none;
            color:var(--ink); font-size:1rem; -webkit-tap-highlight-color:transparent; }
  .action:last-child { border-bottom:0; }
  .action:active { background:#f4f6f7; }
  .action__icon { width:1.75rem; height:1.75rem; flex:0 0 auto; display:grid;
                  place-items:center; border-radius:.5rem; background:var(--pt-teal);
                  color:#fff; font-size:.9rem; font-weight:600; }
  .action__icon--li { background:#0a66c2; }
  .action__icon--save { background:var(--pt-slate); }
  .action__chev { margin-left:auto; color:#b9c0c5; }
  .hint { margin:1.25rem .25rem 0; font-size:.8125rem; line-height:1.5; color:var(--muted); }
  .hint b { color:var(--ink); font-weight:600; }
  @media (prefers-color-scheme: dark) {
    body { background:#000; }
    .hint { color:#8b949a; }
  }
</style>
</head>
<body>
<main class="wrap">
  <div class="sheet">
    <article class="card">
      <img class="card__wordmark" src="assets/parker-wordmark.svg" alt="Parker Technology">
      <div class="card__identity">
        <h1 class="card__name">Dhruv Bangera</h1>
        <p class="card__title">AI Engineer</p>
        <p class="card__company">Parker Technology</p>
      </div>
      <figure class="card__qr">
        <img src="assets/qr.svg" alt="QR code linking to this page" width="160" height="160">
        <figcaption class="card__scan">Scan to connect</figcaption>
      </figure>
    </article>

    <nav class="actions">
      <a class="action" href="dhruv.vcf">
        <span class="action__icon action__icon--save">&#9679;</span>
        Save to Contacts
        <span class="action__chev">&rsaquo;</span>
      </a>
      <a class="action" href="mailto:dhruv.bangera@parkertechnology.com">
        <span class="action__icon">&#9993;</span>
        Email me
        <span class="action__chev">&rsaquo;</span>
      </a>
      <a class="action" href="https://www.linkedin.com/in/dhruvbangera" target="_blank" rel="noopener">
        <span class="action__icon action__icon--li">in</span>
        Connect on LinkedIn
        <span class="action__chev">&rsaquo;</span>
      </a>
    </nav>
  </div>

  <p class="hint" id="a2hs" hidden>
    Keep this card: tap <b>Share</b>, then <b>Add to Home Screen</b>.
  </p>
</main>
<script>
  // Teach Add to Home Screen only on iOS Safari, and only when not already installed.
  // iOS gives no programmatic install prompt, so this is the only available affordance.
  (function () {
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    var standalone = window.navigator.standalone === true ||
      window.matchMedia('(display-mode: standalone)').matches;
    if (isIOS && !standalone) document.getElementById('a2hs').hidden = false;
  })();
</script>
</body>
</html>
```

- [ ] **Step 4: Write the manifest**

```json
{
  "name": "Dhruv Bangera — Parker Technology",
  "short_name": "Dhruv Bangera",
  "start_url": "./",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ffffff",
  "icons": [
    { "src": "assets/icon-180.png", "sizes": "180x180", "type": "image/png" }
  ]
}
```

- [ ] **Step 5: Run the tests and watch them pass**

```bash
build/.venv/bin/python -m pytest tests/ -v
```

Expected: 16 passed.

- [ ] **Step 6: Commit**

```bash
git add site/index.html site/manifest.webmanifest tests/test_page.py
git commit -m "feat: recipient page — card, Contacts/email/LinkedIn, A2HS hint"
```

---

## Task 6: Render the icon, then embed it in the vCard

`icon-180.png` serves two purposes: the Add-to-Home-Screen icon, and the vCard `PHOTO`
so Dhruv shows up in Contacts with the Parker mark. The **square** mark is used because
iOS crops contact photos to a circle.

**Files:**
- Create: `site/assets/icon-180.png`; Modify: `site/dhruv.vcf`; Modify: `tests/test_vcard.py`

- [ ] **Step 1: Start a local server**

**The Playwright MCP blocks the `file:` protocol** — verified, it errors with
"Access to file: protocol is blocked". Everything must be served over HTTP.

```bash
cd /Users/dhruvbangera/Desktop/Digital_Business_Card
python3 -m http.server 8137 --bind 127.0.0.1 &
sleep 1 && curl -s -o /dev/null -w 'server: %{http_code}\n' http://localhost:8137/site/index.html
```

- [ ] **Step 2: Render the icon with the Playwright MCP**

Write `out/icon.html` (`out/` is gitignored, so harnesses never pollute the repo):

```html
<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;width:180px;height:180px;background:#fff;}
img{width:180px;height:180px;display:block;}</style>
<img src="../site/assets/parker-mark.svg">
```

Then, using the Playwright MCP:
`browser_resize` to 180×180 → `browser_navigate` to
`http://localhost:8137/out/icon.html` → `browser_take_screenshot` with
`filename` set to the **absolute** path
`/Users/dhruvbangera/Desktop/Digital_Business_Card/site/assets/icon-180.png`.

**The filename must be absolute.** A relative path resolves against the browser's own
working directory — it lands in the repo root, not where you intend. Verified the hard
way: it left a stray PNG at the repo root.

- [ ] **Step 3: Verify dimensions**

```bash
build/.venv/bin/python -c "
from PIL import Image; im=Image.open('site/assets/icon-180.png'); print(im.size, im.mode)
assert im.size==(180,180), im.size; print('OK')"
```

Expected: `(180, 180) RGBA` then `OK`

- [ ] **Step 4: Add the failing PHOTO test**

Append to `tests/test_vcard.py`:

```python
def test_photo_embedded_as_base64_png():
    """Parker mark appears as the contact photo in iOS Contacts."""
    t = VCF.read_text()
    assert "PHOTO;ENCODING=b;TYPE=PNG:" in t


def test_photo_folded_to_75_octets():
    """RFC 6350: lines over 75 octets must be folded with CRLF + single space,
    or Apple Contacts truncates the photo."""
    for raw in VCF.read_bytes().split(b"\r\n"):
        assert len(raw) <= 75, f"unfolded line of {len(raw)} octets"
```

- [ ] **Step 5: Run it and watch it fail**

```bash
build/.venv/bin/python -m pytest tests/test_vcard.py -v
```

Expected: FAIL — no `PHOTO` line.

- [ ] **Step 6: Regenerate the vCard with a folded PHOTO**

```bash
build/.venv/bin/python - <<'PY'
import base64, textwrap
from pathlib import Path

photo = base64.b64encode(Path("site/assets/icon-180.png").read_bytes()).decode()
lines = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    "N:Bangera;Dhruv;;;",
    "FN:Dhruv Bangera",
    "ORG:Parker Technology",
    "TITLE:AI Engineer",
    "EMAIL;type=INTERNET;type=WORK;type=pref:dhruv.bangera@parkertechnology.com",
    "URL;type=WORK:https://dhruvbangera.github.io",
    "X-SOCIALPROFILE;type=linkedin;x-user=dhruvbangera:https://www.linkedin.com/in/dhruvbangera",
]
# Fold: first line carries the property name, continuations get a single leading space.
first = "PHOTO;ENCODING=b;TYPE=PNG:" + photo
wrapped = textwrap.wrap(first, 74, drop_whitespace=False, break_long_words=True)
lines.append(wrapped[0])
lines.extend(" " + w for w in wrapped[1:])
lines.append("END:VCARD")

Path("site/dhruv.vcf").write_bytes(("\r\n".join(lines) + "\r\n").encode())
print("vcf bytes:", Path("site/dhruv.vcf").stat().st_size)
PY
```

- [ ] **Step 7: Run the full suite and watch it pass**

```bash
build/.venv/bin/python -m pytest tests/ -v
```

Expected: 18 passed. The no-phone and single-b guards must still pass.

- [ ] **Step 8: Commit**

```bash
git add site/assets/icon-180.png site/dhruv.vcf tests/test_vcard.py
git commit -m "feat: embed Parker mark as vCard PHOTO + apple-touch-icon

Square mark, not the wordmark — iOS crops contact photos to a circle.
Base64 folded to 75 octets per RFC 6350 or Contacts truncates it."
```

---

## Task 7: Deploy to GitHub Pages via Actions

The QR encodes the live URL, so **the site must be live before the card image is rendered.**
Reversing this ships a beautiful card with a dead QR.

Deploying with a workflow (rather than serving a branch root) means `site/` publishes while
`build/`, `tests/` and `docs/` stay out of the public site, and every later push redeploys
automatically with no force-pushes.

**Files:**
- Create: `.github/workflows/pages.yml`

- [ ] **Step 1: Create the public repo**

The repo must be **named** `dhruvbangera.github.io` for Pages to serve it at the root
domain. Free-tier Pages requires public.

```bash
gh repo create dhruvbangera.github.io --public \
  --description "Digital business card — Dhruv Bangera, AI Engineer, Parker Technology" \
  --source=. --remote=origin
```

- [ ] **Step 2: Write the deploy workflow**

```yaml
# .github/workflows/pages.yml
name: Deploy Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: Point Pages at the workflow and push**

```bash
git add -A
git commit -m "ci: deploy site/ to Pages via Actions"
git push -u origin main

gh api -X POST repos/dhruvbangera/dhruvbangera.github.io/pages \
  -f build_type=workflow 2>/dev/null \
  || gh api -X PUT repos/dhruvbangera/dhruvbangera.github.io/pages \
       -f build_type=workflow
```

- [ ] **Step 4: Watch the deploy finish**

```bash
gh run watch --exit-status $(gh run list --workflow=pages.yml --limit 1 --json databaseId -q '.[0].databaseId')
```

Expected: the run completes successfully. If it fails, read the log with
`gh run view --log-failed`.

- [ ] **Step 5: Verify the site is live**

```bash
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' https://dhruvbangera.github.io/)
  echo "attempt $i: $code"
  [ "$code" = "200" ] && break
  sleep 10
done
```

Expected: eventually `200`. The very first Pages build can take several minutes.

- [ ] **Step 6: Verify the vCard MIME type**

This single check decides whether the native Contacts sheet appears at all.

```bash
curl -sI https://dhruvbangera.github.io/dhruv.vcf | grep -i '^content-type'
```

Expected: `content-type: text/vcard`.

If it returns `application/octet-stream`, iOS downloads the file instead of offering
Contacts. Record it as a known issue and continue — it does not block the remaining
tasks, and the fix (a `_headers` file or serving via a different host) is out of scope here.

- [ ] **Step 7: Confirm assets resolve**

```bash
for f in card.css dhruv.vcf assets/qr.svg assets/parker-wordmark.svg assets/icon-180.png manifest.webmanifest; do
  printf '%-32s %s\n' "$f" "$(curl -s -o /dev/null -w '%{http_code}' https://dhruvbangera.github.io/$f)"
done
```

Expected: `200` for every row. A `404` here means the card renders unstyled or the QR is
missing on the live page.

---

## Task 8: Render the card image and decode-verify the QR

Renders at exact pixel dimensions for an iPhone 16 Pro (402×874 pt @3x = 1206×2622 px)
by scaling CSS, avoiding a `deviceScaleFactor` that would require installing chromium.

**Files:**
- Create: `build/shot.html`, `build/verify.py`, `out/card@3x.png`

- [ ] **Step 1: Write the shot page**

```html
<!-- build/shot.html — screenshot harness. Reuses site/card.css verbatim. -->
<!doctype html>
<html lang="en" class="shot">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="../site/card.css">
<style>
  /* 3x everything so a 1x screenshot yields true @3x pixels. */
  html { font-size: 48px; }          /* 16px * 3 */
  html, body { width: 1206px; height: 2622px; background: #fff; }
  .card { padding: 8.25rem 6rem 6.75rem; }
  .card__wordmark { width: 28.5rem; }
  .card__qr img { width: 30rem; height: 30rem; }
</style>
</head>
<body>
<article class="card">
  <img class="card__wordmark" src="../site/assets/parker-wordmark.svg" alt="Parker Technology">
  <div class="card__identity">
    <h1 class="card__name">Dhruv Bangera</h1>
    <p class="card__title">AI Engineer</p>
    <p class="card__company">Parker Technology</p>
  </div>
  <figure class="card__qr">
    <img src="../site/assets/qr.svg" alt="">
    <figcaption class="card__scan">Scan to connect</figcaption>
  </figure>
</article>
</body>
</html>
```

- [ ] **Step 2: Render with the Playwright MCP**

The local server from Task 6 must still be running (`python3 -m http.server 8137`).

`browser_resize` to 1206×2622 → `browser_navigate` to
`http://localhost:8137/build/shot.html` → `browser_take_screenshot` with
`fullPage: true`, `scale: "device"`, and `filename` set to the **absolute** path
`/Users/dhruvbangera/Desktop/Digital_Business_Card/out/card@3x.png`.

Both constraints are verified, not assumed: the MCP blocks `file:` URLs, and a relative
`filename` resolves against the browser's working directory (landing in the repo root).

- [ ] **Step 3: Write the verification script**

```python
# build/verify.py
"""Decode the QR back out of the FINAL rendered image.
Generation-time success does not prove render-time success: scaling and
anti-aliasing in the browser can destroy a QR that was fine as an SVG."""
import sys
import cv2

URL = "https://dhruvbangera.github.io"
PATH = "out/card@3x.png"

img = cv2.imread(PATH)
if img is None:
    sys.exit(f"FAIL: could not read {PATH}")

got, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
h, w = img.shape[:2]
print(f"image:   {w}x{h}")
print(f"decoded: {got!r}")

if got != URL:
    sys.exit(f"FAIL: expected {URL!r}. If blank, the QR anti-aliased badly — "
             f"re-run build.py with dark='#000000' and re-render.")
if (w, h) != (1206, 2622):
    sys.exit(f"FAIL: expected 1206x2622, got {w}x{h}")
print("PASS: QR decodes from the final render at correct dimensions")
```

- [ ] **Step 4: Run it**

```bash
build/.venv/bin/python build/verify.py
```

Expected:
```
image:   1206x2622
decoded: 'https://dhruvbangera.github.io'
PASS: QR decodes from the final render at correct dimensions
```

If it fails, edit `build/build.py` to use `dark="#000000"`, re-run `build.py`, re-render,
re-verify. **Function beats brand color.**

- [ ] **Step 5: Commit**

```bash
git add build/shot.html build/verify.py
git commit -m "feat: 3x card render + QR decode verification from final image

Verifies the rendered PNG, not the source SVG — browser anti-aliasing can
break a QR that generated fine."
```

---

## Task 9: iPhone setup guide and parked pass

**Files:**
- Create: `SHORTCUT.md`, `site/pass.json`, `CLAUDE.md`

- [ ] **Step 1: Write `SHORTCUT.md`**

````markdown
# iPhone setup (~2 minutes)

## 1. Get the card onto your phone

AirDrop `out/card@3x.png` from this Mac to your iPhone. It lands in Photos.

Then: Photos → select it → **Add to Album** → **New Album** → name it exactly
`Business Card`. The Shortcut looks the album up by that name.

## 2. Build the Shortcut

Shortcuts app → **+** → add two actions, in this order:

1. **Find Photos** — set *Album* `is` `Business Card`, and *Limit* to `1` photo.
2. **Quick Look** — takes the result of the previous action.

Name it `Business Card`. Give it the Parker teal color if you like.

## 3. Bind it to the Action Button

Settings → **Action Button** → swipe to **Shortcut** → Choose a Shortcut →
`Business Card`.

**Press and hold** the Action Button. It is a hold, not a click.

### Alternates (both free, both native)

- **Back Tap** — Settings → Accessibility → Touch → Back Tap → Double Tap → `Business Card`.
  This is literally a double-tap, if that is the gesture you originally wanted.
- **Lock Screen** — long-press the Lock Screen → Customize → replace the flashlight or
  camera button with the Shortcut.

---

# On-device checklist

These **cannot be verified from a Mac**. Confirm each before handing the card to anyone.

- [ ] Action Button press-and-hold shows the card full-screen
- [ ] It still works in Airplane Mode (proves it is genuinely offline)
- [ ] A second phone's Camera app scans the QR from your screen at arm's length
- [ ] The QR opens `https://dhruvbangera.github.io` in **Safari**, not inside another app
- [ ] **Save to Contacts** opens the native iOS Add Contact sheet
- [ ] The saved contact shows the Parker mark as its photo
- [ ] **Email me** opens Mail with the address filled in
- [ ] **Connect on LinkedIn** opens the LinkedIn app and lands on the right profile
      — this is the one thing no automated check could verify
- [ ] Share → Add to Home Screen creates an icon that opens with no Safari address bar

Screen brightness matters for QR scanning. Turn it up before showing the card.
````

- [ ] **Step 2: Park the unsigned pass**

```json
{
  "formatVersion": 1,
  "passTypeIdentifier": "pass.com.parkertechnology.businesscard",
  "teamIdentifier": "REPLACE_WITH_TEAM_ID",
  "organizationName": "Parker Technology",
  "description": "Dhruv Bangera — AI Engineer",
  "serialNumber": "dhruv-bangera-001",
  "backgroundColor": "rgb(255,255,255)",
  "foregroundColor": "rgb(11,12,12)",
  "labelColor": "rgb(2,81,114)",
  "logoText": "Parker Technology",
  "barcodes": [
    {
      "format": "PKBarcodeFormatQR",
      "message": "https://dhruvbangera.github.io",
      "messageEncoding": "iso-8859-1"
    }
  ],
  "generic": {
    "primaryFields": [
      { "key": "name", "label": "", "value": "Dhruv Bangera" }
    ],
    "secondaryFields": [
      { "key": "title", "label": "TITLE", "value": "AI Engineer" }
    ],
    "auxiliaryFields": [
      { "key": "company", "label": "COMPANY", "value": "Parker Technology" }
    ],
    "backFields": [
      { "key": "email", "label": "Email", "value": "dhruv.bangera@parkertechnology.com" },
      { "key": "linkedin", "label": "LinkedIn", "value": "https://www.linkedin.com/in/dhruvbangera" }
    ]
  }
}
```

- [ ] **Step 3: Write `CLAUDE.md`**

```markdown
# Digital Business Card

Zero-cost native digital business card. Presenter side is an offline image shown via
the iPhone Action Button; recipient side is a GitHub Pages site with a vCard.

## Constraints — verified, do not re-litigate

- **No Apple Wallet pass.** `.pkpass` requires a $99/yr Apple Developer Pass Type ID
  certificate. This machine has 0 signing identities and no WWDR intermediate.
  `site/pass.json` is parked unsigned; if a Developer account ever appears, signing it
  is ~10 minutes and needs no rebuild.
- **Camera Control cannot run arbitrary Shortcuts.** Only the Action Button, Back Tap,
  and Lock Screen controls can. Do not "fix" this.
- **GitHub is the only authenticated host** (`vercel` and `render` are installed but
  logged out). Hosting is GitHub Pages.
- **No phone number**, by explicit decision. `tests/test_vcard.py` enforces it.
- **LinkedIn is `dhruvbangera`, single b.** LinkedIn returns HTTP 999 for every
  spelling, so no network check can catch a typo — only the test guard can.

## Commands

    build/.venv/bin/python build/build.py      # regenerate assets
    build/.venv/bin/python -m pytest tests/ -v # full suite
    build/.venv/bin/python build/verify.py     # decode QR from final render

## Rules

- The card is ONE component (`site/card.css`). The page and the screenshot both use it.
  Never fork it.
- Deploy before rendering the image — the QR encodes the live URL.
- If the QR fails to decode after rendering, switch `dark` to `#000000` in `build.py`.
  Function beats brand color.
```

- [ ] **Step 4: Run the full suite one last time**

```bash
build/.venv/bin/python -m pytest tests/ -v && build/.venv/bin/python build/verify.py
```

Expected: 18 passed, then `PASS: QR decodes from the final render`.

- [ ] **Step 5: Commit and push**

```bash
git add SHORTCUT.md site/pass.json CLAUDE.md
git commit -m "docs: iPhone setup, on-device checklist, parked unsigned pass"
git push origin main
```

---

## Definition of done

**Verified on this machine:**
- [ ] 18 tests pass
- [ ] QR decodes to exactly `https://dhruvbangera.github.io` from the final 1206×2622 render
- [ ] `https://dhruvbangera.github.io/` returns 200 over HTTPS
- [ ] `dhruv.vcf` content-type recorded (`text/vcard` expected)

**Requires Dhruv's iPhone — explicitly NOT claimed as done by this plan:**
- [ ] Action Button fires the Shortcut
- [ ] Contacts sheet opens from Safari
- [ ] QR scans off-screen at real distance
- [ ] LinkedIn lands on the right profile

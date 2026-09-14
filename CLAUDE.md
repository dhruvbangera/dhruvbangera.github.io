# Digital Business Card

Zero-cost native digital business card for Dhruv Bangera, AI Engineer, Parker Technology.

- **Presenter side:** an offline image shown full-screen via the iPhone Action Button.
- **Recipient side:** a GitHub Pages site reached by scanning the card's QR.

## Commands

    build/.venv/bin/python build/build.py       # regenerate brand assets + QR
    build/.venv/bin/python -m pytest tests/ -v  # full suite (19 tests)
    build/.venv/bin/python build/verify.py      # decode QR from the final render

To re-render the card image (`out/card@3x.png`):

    python3 -m http.server 8137 --bind 127.0.0.1 &
    # Playwright MCP: resize 1206x2622 -> navigate http://localhost:8137/build/shot.html
    # -> screenshot, scale "css", to an ABSOLUTE path
    build/.venv/bin/python build/verify.py

## Constraints — verified, do not re-litigate

- **No Apple Wallet pass.** A `.pkpass` requires a $99/yr Apple Developer Pass Type ID
  certificate. This machine has 0 signing identities and no WWDR intermediate.
  `site/pass.json` is parked unsigned; if a Developer account ever appears, signing it
  is ~10 minutes and needs no rebuild.
- **Camera Control cannot run arbitrary Shortcuts.** Only the Action Button, Back Tap,
  and Lock Screen controls can. Do not "fix" this.
- **The Playwright MCP blocks `file:` URLs.** Serve over `python3 -m http.server`.
  Screenshot filenames must be **absolute** — a relative path resolves against the
  browser's working directory and lands in the repo root.
- **Pillow is not in the venv** (system Python only). Use `cv2` for image checks.
- **GitHub is the only authenticated host** — `vercel` and `render` are installed but
  logged out. Hosting is GitHub Pages.
- **No phone number**, by explicit decision. `tests/test_vcard.py` enforces it.
- **LinkedIn is `dhruvbangera`, single b.** LinkedIn returns HTTP 999 for every
  spelling, so no network check can catch a typo — only the test guard can.
- **The camera banner cannot be aliased.** It shows the real URL by design. Encoding a
  vCard instead would show the name but costs 2.4x QR density and drops the page.
  Considered and declined; see `SHORTCUT.md`.

## Rules

- The card is **one component** (`site/card.css`). The live page and the 3x screenshot
  both use it. Never fork it. `build/shot.html` deliberately defines no sizes — it only
  sets the root font-size to 3x, so every `rem` scales exactly once. Overriding widths
  there double-scales them.
- **Deploy before rendering** if the URL ever changes — the QR encodes it.
- **QR quiet zone is load-bearing.** `border=4` in `build.py`. `border=0` was shipped
  once and does not decode at all; the test passed anyway because it decoded a
  *different* file. `qr.svg` and `qr-check.png` now share one options dict so they
  cannot drift. If a render ever fails to decode, switch `dark` to `#000000` —
  function beats brand color.
- **vCard tests read the UNFOLDED card.** RFC 6350 folding splits long values across
  lines; asserting on raw bytes silently blinds the single-b guard. Property checks
  match line *starts*, not substrings, because `TEL` can occur inside the base64 photo.
- **Actions follow the iOS Contacts idiom**, not the Settings idiom: circular tinted
  buttons with captions for actions, label-over-value rows for data, and no chevrons
  (a chevron means "drills into another screen"). Do not restyle these as Settings
  rows with colored square chips.
- **Icons are inline SVG, not dingbat characters.** `&#9679;` and `&#9993;` render
  inconsistently across platforms. Do not "simplify" them back.

## Not verified from this machine

The Action Button firing, the Contacts sheet opening, the QR scanning off a real
screen, and the LinkedIn URL landing on the right profile all require a physical
iPhone. See the checklist in `SHORTCUT.md`. Do not report these as working.

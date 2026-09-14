# Digital Business Card — Design

**Date:** 2026-09-14
**Status:** Approved, pending implementation plan
**Owner:** Dhruv Bangera

## Problem

Dhruv wants a one-press gesture on an iPhone 16 Pro that displays his business card,
and a QR code on that card that gives the other person something they can keep.

The original request specified Apple Wallet and a `.pkpass`, triggered by double-clicking
the side button.

## Why not Apple Wallet

A `.pkpass` is not a writable file format. iOS validates a cryptographic signature on
every pass: a `manifest.json` signed with an Apple-issued **Pass Type ID certificate**,
chained to Apple's WWDR intermediate. Unsigned or self-signed passes are rejected by
Wallet silently — no error dialog, the pass simply does not add.

Obtaining that certificate requires Apple Developer Program membership at $99/yr.
Verified on this machine: `security find-identity -v -p codesigning` returns
**0 valid identities**, and the WWDR intermediate is **not installed**.

The decision was to not spend $99. This is correct, because the `.pkpass` was only ever
a *delivery mechanism for a picture of a card*. The same outcome is reachable with
zero cost and equally native components.

**The door stays open.** `pass.json` ships in this repo unsigned. If Parker Technology
turns out to hold a Developer Program membership, signing it is a ~10 minute job
requiring no rebuild.

## Trigger research (verified, not assumed)

| Surface | Location | Can run an arbitrary Shortcut? |
|---|---|---|
| **Action Button** | left side, above volume | **Yes** — Settings › Action Button › Shortcut. **Press-and-hold**, not a click. |
| Camera Control | right side, lower | **No.** Apple only exposes "which camera app to launch." The community workaround (point it at a third-party app + a Shortcuts automation on `App Is Opened`) visibly launches that app first. Rejected as not seamless. |
| Back Tap | Accessibility › Touch › Back Tap | **Yes** — double- or triple-tap the back of the phone. Closest to the originally-described "double tap." |
| Control Center / Lock Screen | iOS 18 Controls | **Yes** — can replace the flashlight or camera Lock Screen button. |

**Chosen primary:** Action Button. **Documented alternates:** Back Tap, Lock Screen control.

Sources:
- https://support.apple.com/guide/shortcuts/run-shortcuts-with-the-action-button-apdfea15680b/ios
- https://www.applevis.com/guides/taking-control-camera-control-guide-running-any-shortcut-camera-control-iphone-16

## Architecture

Two halves sharing exactly one string (the URL). Either can be rebuilt without
touching the other.

```
PRESENTER (offline)                  RECIPIENT (network)
─────────────────────                ─────────────────────
Action Button (press+hold)           native Camera scans QR
   │                                    │
   ▼                                    ▼
Shortcut, 2 actions:                 Safari → dhruvbangera.github.io
  Find Photos                           │
    album = "Business Card"             ▼
  Quick Look                         identical card, then:
   │                                   [ Save to Contacts ]  → .vcf
   ▼                                   [ Email ]             → mailto:
full-screen native viewer              [ LinkedIn ]          → app or web
card + QR, works with no signal        hint: Add to Home Screen
```

### Single source of truth

The card is **one HTML/CSS component**. `index.html` renders it live for the recipient;
Playwright screenshots that same component at 3x to produce the presenter's image.
They cannot drift, because they are the same code.

This also removes the need for an SVG rasterizer — headless Chrome is the renderer.
Verified absent on this machine: `rsvg-convert`, `inkscape`, `magick`, `cairosvg`, `resvg`.

## Brand assets (sourced, not invented)

Parker Technology publishes only a **reversed** (white) logo at
`https://parkertechnology.com/media/parker-technology-logo-reversed.svg`.
All standard-variant paths probed return 404.

Colors extracted from that SVG and from `parker-technology-site-icon.svg`:

| Hex | Role |
|---|---|
| `#025172` | Parker deep teal — the mark on light backgrounds |
| `#6697a9` | slate blue accent |
| `#e3d71d` | signal yellow accent |

Because the logo is vector, recoloring `fill:#fff` → `#025172` for a white card is
lossless. Yellow and slate accents are preserved unmodified.

Tagline "Every exception, handled." is **deliberately omitted** — it is Parker's line,
not Dhruv's, and the card reads more confidently with fewer words.

## Card content

Traditional business-card hierarchy, stacked:

```
Dhruv Bangera        name, most prominent
AI Engineer          title
Parker Technology    company
```

Plus the Parker mark and the QR code. White background. `-apple-system` type stack,
which resolves to **SF Pro** on Apple devices — the real system font.

**No phone number**, by explicit decision. A QR in the wild cannot be retracted.

## Contact data

| Field | Value |
|---|---|
| Name | Dhruv Bangera |
| Title | AI Engineer |
| Company | Parker Technology |
| Email | dhruv.bangera@parkertechnology.com |
| LinkedIn | https://www.linkedin.com/in/dhruvbangera |
| Card URL | https://dhruvbangera.github.io |
| Phone | *(omitted by decision)* |

LinkedIn handle corrected by Dhruv on 2026-09-14 from `dhruvbbangera` to
`dhruvbangera` (single b). LinkedIn returns HTTP **999** (its bot-block) rather than
404 for both spellings, so the URL is **not machine-verifiable from here** — a wrong
handle would have looked identical to a right one. Confirm by tapping the live link
on a real device before handing the card to anyone.

## Hosting

GitHub Pages at `https://dhruvbangera.github.io`, from a **public** repo
(free-tier Pages requires public).

Chosen because GitHub is the **only authenticated host** on this machine:

| CLI | Installed | Authenticated |
|---|---|---|
| GitHub | yes | **yes** — `dhruvbangera`, scopes `repo`, `workflow` |
| Vercel 50.4.5 | yes | no — "No existing credentials found" |
| Render v2.20.0 | yes | no — token returns `401 Unauthorized` |

**The QR is not a one-way door.** If a custom domain (e.g. `dhruv.parkertechnology.com`)
is added later, GitHub Pages redirects the `.github.io` URL to it. Existing QR codes
keep working.

## File layout

Local working directory is `~/Desktop/Digital_Business_Card`. It is pushed to the
GitHub repo **named** `dhruvbangera.github.io` (the repo name is what makes Pages
serve it at the root domain). The local folder name does not need to match.

```
Digital_Business_Card/               → pushed to repo "dhruvbangera.github.io"
├── site/                            ← ONLY this dir is published
│   ├── index.html                   card + 3 actions, self-contained
│   ├── card.css                     the one shared component
│   ├── dhruv.vcf                    vCard 3.0, Parker mark as PHOTO
│   ├── manifest.webmanifest         Add to Home Screen
│   ├── pass.json                    unsigned, parked
│   └── assets/
│       ├── parker-wordmark.svg      recolored #fff → #025172
│       ├── parker-mark.svg          square 500x500, used as-is
│       ├── qr.svg                   segno, error-correction H
│       ├── qr-check.png             PNG twin, for the decode test
│       └── icon-180.png             apple-touch-icon + vCard PHOTO
├── build/
│   ├── requirements.txt             pinned deps
│   ├── build.py                     recolor logo, generate QR
│   ├── shot.html                    screenshot harness, reuses card.css
│   └── verify.py                    decode QR from the final render
├── tests/
│   ├── test_assets.py               logo recolor + QR decode
│   ├── test_vcard.py                vCard, no-phone + single-b guards
│   └── test_page.py                 required links present
├── .github/workflows/pages.yml      deploys site/ only
├── out/card@3x.png                  the AirDrop artifact (gitignored)
├── SHORTCUT.md                      iPhone setup + on-device checklist
└── CLAUDE.md                        constraints for future sessions
```

`build/`, `tests/` and `docs/` are deliberately **not** published — the Pages workflow
uploads `site/` only.

## Recipient actions, in priority order

1. **Save to Contacts** — `dhruv.vcf` served as `text/vcard`, handing off to the
   **native iOS Add Contact sheet**. Syncs via iCloud, survives phone upgrades,
   works identically on Android. Embeds the Parker mark as `PHOTO` so Dhruv appears
   in Contacts with the logo.
2. **Email** — `mailto:` to the default mail app.
3. **LinkedIn** — deep link; iOS hands off to the LinkedIn app when installed.
4. **Add to Home Screen** — dismissible hint, shown only on iOS Safari and only when
   not already running standalone. Cannot be triggered from JavaScript; must be taught.

## Build dependencies to install

Verified absent: no QR generator (`qrcode`, `segno`, `qrencode`), no SVG rasterizer.
Present: Pillow 11.3.0, npx, Playwright MCP.

- `segno` — pure-Python QR, emits SVG directly, no native deps
- `opencv-python-headless` — QR **decoding**, for verification
- Playwright — rendering via the **already-installed Playwright MCP**. Verified: only
  `mcp-chrome-*` builds exist in the Playwright cache, so `npx playwright install
  chromium` (~150MB) is avoided. `build/shot.html` scales the card's CSS 3x so a 1x
  screenshot yields true @3x pixels, removing any need for `deviceScaleFactor`.

## Verification

Machine-verifiable here, with output shown:

| Check | Method |
|---|---|
| QR decodes to exactly `https://dhruvbangera.github.io` | render PNG → OpenCV `QRCodeDetector` → assert exact string |
| vCard valid, iOS-required fields present | parse and assert |
| `.vcf` serves as `text/vcard` | `curl -I` against live Pages |
| Page live over HTTPS | `curl` status |
| Card renders correctly | Playwright screenshot, visual review |

**Requires a physical iPhone — will NOT be claimed as verified:**

1. Action Button → Shortcut fires
2. Contacts sheet opens from Safari
3. QR scans off a screen at real-world distance

A checklist for these three ships in `SHORTCUT.md`.

## Build order

The QR encodes the live URL, so **the page deploys before the image renders**.
Reversing this produces a beautiful card with a dead QR.

1. Repo + assets (recolored logo, QR)
2. `card.css` + `index.html`
3. `dhruv.vcf`
4. Deploy to Pages, verify live
5. Playwright render `card@3x.png`, **decode-verify the QR**
6. `SHORTCUT.md` + AirDrop instructions
7. `pass.json` parked

## Risks

| Risk | Mitigation |
|---|---|
| QR in `#025172` may not scan reliably | Decode-verify the final render. **Falls back to black** — function beats aesthetics. |
| Screen glare degrades scanning vs. print | Error-correction level H for margin |
| Repo must be public | Accepted; content is intentionally public |
| LinkedIn URL unverifiable from here | Confirmed by tap test on device |

## Out of scope

- Apple Wallet signing (parked, not abandoned)
- Google Wallet
- Pass update web service
- Analytics on scans
- Multiple cards / other employees

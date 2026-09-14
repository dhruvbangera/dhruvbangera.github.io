# iPhone setup (~2 minutes)

## 1. Get the card onto your phone

AirDrop **`out/card@3x.png`** from this Mac to your iPhone. It lands in Photos.

> Not in git — it's a build artifact. Regenerate any time with the steps in `CLAUDE.md`.

Then: Photos → select it → **Add to Album** → **New Album** → name it exactly
`Business Card`. The Shortcut looks the album up by that name, so the spelling matters.

## 2. Build the Shortcut

Shortcuts app → **+** → add two actions, in this order:

1. **Find Photos** — set *Album* `is` `Business Card`, and *Limit* to `1` photo.
2. **Quick Look** — takes the result of the previous action.

Name it `Business Card`.

Quick Look is a native full-screen iOS viewer, and the image is local, so this works
with no signal — which, given Parker's business, is not a hypothetical.

## 3. Bind it to the Action Button

Settings → **Action Button** → swipe to **Shortcut** → Choose a Shortcut →
`Business Card`.

**Press and hold** the Action Button. It is a hold, not a click.

### Alternates (both free, both native)

- **Back Tap** — Settings → Accessibility → Touch → Back Tap → Double Tap →
  `Business Card`. This is literally a double-tap, if that's the gesture you
  originally pictured.
- **Lock Screen** — long-press the Lock Screen → Customize → replace the flashlight
  or camera button with the Shortcut.

### Not an option

**Camera Control** (the button on the lower right) cannot run arbitrary Shortcuts.
Apple only exposes "which camera app to launch." The workaround floating around —
point it at a third-party app, then trigger a Shortcuts automation on "App Is
Opened" — visibly launches that other app first. It was tried and rejected.

---

# On-device checklist

**These cannot be verified from a Mac.** Everything below is unproven until you
check it. Do this before handing the card to anyone.

- [ ] Action Button press-and-hold shows the card full-screen
- [ ] It still works in **Airplane Mode** (proves it's genuinely offline)
- [ ] A second phone's Camera app scans the QR from your screen at arm's length
- [ ] The QR opens `https://dhruvbangera.github.io` in **Safari**
- [ ] **add contact** opens the native iOS Add Contact sheet
- [ ] The saved contact shows the Parker mark as its photo
- [ ] **mail** opens Mail with the address filled in
- [ ] **linkedin** opens the LinkedIn app on the right profile —
      **no automated check could verify this.** LinkedIn returns HTTP 999 to every
      request, so a wrong handle looks identical to a right one to any script.
      You are the only verification this has.
- [ ] Share → **Add to Home Screen** creates an icon that opens with no Safari
      address bar

Turn screen brightness up before showing the card — it materially affects whether
the QR scans.

---

# What the camera banner says

Scanning shows `dhruvbangera.github.io` for about a second before Safari opens.

That **cannot** be changed to read "Dhruv Bangera - Card". iOS deliberately shows the
real destination; letting anyone put arbitrary text over a URL is the phishing vector
that design prevents. No QR format or host overrides it.

Your name does appear everywhere after that second: the page title, the Home Screen
icon name, and the saved contact. Encoding the vCard directly in the QR *would* make
the banner read "Dhruv Bangera", but it costs 97 modules instead of 41 — much harder
to scan — and it would no longer open the page at all. Considered and declined.

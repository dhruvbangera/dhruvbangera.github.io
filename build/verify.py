# build/verify.py
"""Decode the QR back out of the FINAL rendered image.

Generation-time success does not prove render-time success: browser scaling and
anti-aliasing can destroy a QR that was fine as an SVG. This decodes the actual
artifact that goes on the phone.
"""
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
    sys.exit(f"FAIL: expected 1206x2622 (iPhone 16 Pro @3x), got {w}x{h}")
print("PASS: QR decodes from the final render at correct dimensions")

import os
import subprocess
import tempfile
import fontforge

LETTER_DIR = "Letter"
OUTPUT_FONT = "MyFont.ttf"

font = fontforge.font()
font.encoding = "UnicodeFull"

font.fontname = "MyFont"
font.familyname = "MyFont"
font.fullname = "MyFont"

font.em = 1000
font.ascent = 800
font.descent = 200

for filename in sorted(os.listdir(LETTER_DIR)):

    if not filename.lower().endswith(".png"):
        continue

    char = os.path.splitext(filename)[0]

    if len(char) != 1:
        print("Skip", filename)
        continue

    png = os.path.join(LETTER_DIR, filename)

    svg = os.path.join(tempfile.gettempdir(), char + ".svg")

    subprocess.run([
        "vtracer",
        "--input", png,
        "--output", svg,
        "--colormode", "binary"
    ], check=True)

    glyph = font.createChar(ord(char))
    glyph.clear()

    glyph.importOutlines(svg)

    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.simplify()
    glyph.round()

    # バウンディングボックス取得
    xmin, ymin, xmax, ymax = glyph.boundingBox()

    if xmax == xmin or ymax == ymin:
        print("Empty:", char)
        continue

    # EMサイズへ収める
    scale = 750 / max(xmax - xmin, ymax - ymin)

    glyph.transform((
        scale, 0,
        0, scale,
        -xmin * scale + 125,
        -ymin * scale + 125
    ))

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0
    glyph.width = 1000

    print("Added", char)

font.generate(OUTPUT_FONT)

print("Finished")

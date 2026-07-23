import os
import subprocess
import tempfile
import fontforge

LETTER_DIR = "Letter"
OUTPUT_FONT = "MyFont.ttf"

EM = 1000
ASCENT = 800
DESCENT = 200

font = fontforge.font()
font.encoding = "UnicodeFull"

font.fontname = "MyFont"
font.familyname = "MyFont"
font.fullname = "MyFont"

font.em = EM
font.ascent = ASCENT
font.descent = DESCENT

for filename in sorted(os.listdir(LETTER_DIR)):

    if not filename.lower().endswith(".png"):
        continue

    char = os.path.splitext(filename)[0]

    if len(char) != 1:
        print("Skip:", filename)
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

    xmin, ymin, xmax, ymax = glyph.boundingBox()

    if xmax <= xmin or ymax <= ymin:
        print("Empty:", char)
        continue

    width = xmax - xmin
    height = ymax - ymin

    # 高さ800に合わせる
    scale = ASCENT / height

    # 幅が1000を超えるなら幅優先
    if width * scale > EM:
        scale = EM / width

    tx = (EM - width * scale) / 2 - xmin * scale
    ty = -ymin * scale

    glyph.transform((
        scale, 0,
        0, scale,
        tx, ty
    ))

    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.round()

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0
    glyph.width = EM

    print("Added", char)

font.generate(OUTPUT_FONT)
print("Finished")

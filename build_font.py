import os
import subprocess
import tempfile

import fontforge
from PIL import Image
# ==========================
# 設定
# ==========================

INPUT_DIR = "Letter"
TEMP_DIR = os.path.join(tempfile.gettempdir(), "LetterTransparent")
OUTPUT_FONT = "MyFont.ttf"

THRESHOLD = 240

EM = 100
ASCENT = 80
DESCENT = 20

os.makedirs(TEMP_DIR, exist_ok=True)

# ==========================
# FontForge
# ==========================

font = fontforge.font()
font.encoding = "UnicodeFull"

font.fontname = "MyFont"
font.familyname = "MyFont"
font.fullname = "MyFont"

font.em = EM
font.ascent = ASCENT
font.descent = DESCENT

# ==========================
# 全画像処理
# ==========================

for filename in sorted(os.listdir(INPUT_DIR)):

    if not filename.lower().endswith(".png"):
        continue

    char = os.path.splitext(filename)[0]

    if len(char) != 1:
        print("Skip:", filename)
        continue

    input_png = os.path.join(INPUT_DIR, filename)

    # --------------------------
    # 白を透明化
    # --------------------------

    img = Image.open(input_png).convert("RGBA")

    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):

            r, g, b, a = pixels[x, y]

            if r >= THRESHOLD and g >= THRESHOLD and b >= THRESHOLD:
                pixels[x, y] = (255, 255, 255, 0)
            else:
                pixels[x, y] = (0, 0, 0, 255)

    clean_png = os.path.join(TEMP_DIR, filename)
    img.save(clean_png)

    # --------------------------
    # SVG化
    # --------------------------

    svg = os.path.join(TEMP_DIR, char + ".svg")

    subprocess.run([
        "vtracer",
        "--input", clean_png,
        "--output", svg,
        "--colormode", "binary"
    ], check=True)

    # --------------------------
    # FontForge
    # --------------------------

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

    scale = ASCENT / height

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

    print("Added:", char)

# ==========================
# フォント生成
# ==========================

font.generate(OUTPUT_FONT)

print("Finished!")

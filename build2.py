import os
import subprocess
import tempfile

import fontforge
from PIL import Image

# ==========================
# 設定
# ==========================

INPUT_DIR = "f"
TEMP_DIR = os.path.join(tempfile.gettempdir(), "LetterTransparent")
OUTPUT_FONT = "MyFont2.ttf"

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

font.fontname = "MyFont2"
font.familyname = "MyFont2"
font.fullname = "MyFont2"

font.em = EM
font.ascent = ASCENT
font.descent = DESCENT

# ==========================
# 全画像処理
# ==========================

for filename in sorted(os.listdir(INPUT_DIR)):

    if not filename.lower().endswith(".png"):
        continue

    # ".png" を末尾から4文字削除
    # 例:
    # A.png  -> A
    # a.png  -> a
    # 1.png  -> 1
    # ..png  -> .
    char = filename[:-4]

    if len(char) != 1:
        print("Skip:", filename)
        continue

    print("Processing:", filename, "->", repr(char))

    input_png = os.path.join(INPUT_DIR, filename)

    # ==========================
    # Unicodeコードポイント
    # ==========================

    code = ord(char)

    # 一時ファイル名には文字そのものを使わない
    # "." などでも安全に処理できる
    clean_png = os.path.join(
        TEMP_DIR,
        f"clean_U{code:04X}.png"
    )

    svg = os.path.join(
        TEMP_DIR,
        f"glyph_U{code:04X}.svg"
    )

    # ==========================
    # 白を透明化
    # ==========================

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

    # ==========================
    # PNG保存
    # ==========================

    img.save(clean_png, format="PNG")

    # ==========================
    # SVG化
    # ==========================

    subprocess.run([
        "vtracer",
        "--input", clean_png,
        "--output", svg,
        "--colormode", "binary"
    ], check=True)

    # ==========================
    # FontForge
    # ==========================

    glyph = font.createChar(code)
    glyph.clear()

    glyph.importOutlines(svg)

    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.simplify()
    glyph.round()

    # ==========================
    # Bounding Box
    # ==========================

    xmin, ymin, xmax, ymax = glyph.boundingBox()

    if xmax <= xmin or ymax <= ymin:
        print("Empty:", repr(char))
        continue

    width = xmax - xmin
    height = ymax - ymin

    # ==========================
    # サイズ調整
    # ==========================

    scale = ASCENT / height

    if width * scale > EM:
        scale = EM / width

    # ==========================
    # 中央配置
    # ==========================

    tx = (EM - width * scale) / 2 - xmin * scale
    ty = -ymin * scale

    glyph.transform((
        scale,
        0,
        0,
        scale,
        tx,
        ty
    ))

    # ==========================
    # 輪郭修正
    # ==========================

    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.round()

    # ==========================
    # Glyph幅を統一
    # ==========================

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0
    glyph.width = EM

    print("Added:", repr(char), f"(U+{code:04X})")

# ==========================
# フォント生成
# ==========================

font.generate(OUTPUT_FONT)

print("Finished!")
print("Output:", OUTPUT_FONT)

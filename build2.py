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

    # ==========================
    # Glyph文字を取得
    # ==========================
    #
    # A.png  -> A
    # 1.png  -> 1
    # ..png  -> .
    #
    char = filename[:-4]

    if len(char) != 1:
        print("Skip:", filename)
        continue

    code = ord(char)

    print("Processing:", filename, "->", repr(char))

    input_png = os.path.join(INPUT_DIR, filename)

    # ==========================
    # 一時ファイル
    # ==========================

    clean_png = os.path.join(
        TEMP_DIR,
        f"clean_U{code:04X}.png"
    )

    svg = os.path.join(
        TEMP_DIR,
        f"glyph_U{code:04X}.svg"
    )

    # ==========================
    # PNG読み込み
    # ==========================

    img = Image.open(input_png).convert("RGBA")

    pixels = img.load()
    width, height = img.size

    # ==========================
    # 白を透明化
    # ==========================

    for y in range(height):
        for x in range(width):

            r, g, b, a = pixels[x, y]

            if (
                r >= THRESHOLD
                and g >= THRESHOLD
                and b >= THRESHOLD
            ):
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

    # ==========================
    # 輪郭整理
    # ==========================

    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.simplify()
    glyph.round()

    # ==========================
    # 元のGlyphサイズを維持
    # ==========================
    #
    # ここではscaleを計算しない。
    # 元画像からSVG化されたGlyphの
    # 縦横比・形状・サイズをそのまま使用する。
    #
    # ==========================

    xmin, ymin, xmax, ymax = glyph.boundingBox()

    if xmax <= xmin or ymax <= ymin:
        print("Empty:", repr(char))
        continue

    # ==========================
    # 横方向だけ中央配置
    # ==========================
    #
    # サイズ・形状は変更しない。
    # X方向の位置だけ調整する。
    #
    # ==========================

    glyph_width = xmax - xmin

    tx = (EM - glyph_width) / 2 - xmin

    glyph.transform((
        1,
        0,
        0,
        1,
        tx,
        0
    ))

    # ==========================
    # 輪郭整理
    # ==========================

    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.round()

    # ==========================
    # Glyph幅
    # ==========================

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0

    # Glyphの幅だけEMに合わせる
    glyph.width = EM

    print(
        "Added:",
        repr(char),
        f"(U+{code:04X})",
        f"size={glyph_width:.2f}"
    )

# ==========================
# フォント生成
# ==========================

font.generate(OUTPUT_FONT)

print("Finished!")
print("Output:", OUTPUT_FONT)

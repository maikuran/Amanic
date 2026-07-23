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

font.em = 100
font.ascent = 80
font.descent = 20

for filename in sorted(os.listdir(LETTER_DIR)):
    if not filename.lower().endswith(".png"):
        continue

    char = os.path.splitext(filename)[0]

    if len(char) != 1:
        print(f"Skip {filename}")
        continue

    png = os.path.join(LETTER_DIR, filename)

    svg = os.path.join(tempfile.gettempdir(), char + ".svg")

    subprocess.run([
        "vtracer",
        "--input",
        png,
        "--output",
        svg
    ], check=True)

    glyph = font.createChar(ord(char))

    glyph.importOutlines(svg)
    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.simplify()
    glyph.round()

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0
    glyph.width = 1000

    print(f"Added {char}")

font.generate(OUTPUT_FONT)

print("Finished")

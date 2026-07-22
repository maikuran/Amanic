import os
import fontforge

LETTER_DIR = "Letter"
OUTPUT = "MyFont.ttf"

font = fontforge.font()
font.fontname = "MyFont"
font.familyname = "MyFont"
font.fullname = "MyFont"

font.em = 1000
font.ascent = 800
font.descent = 200

for file in sorted(os.listdir(LETTER_DIR)):
    if not file.lower().endswith(".png"):
        continue

    name = os.path.splitext(file)[0]

    if len(name) != 1:
        print(f"Skip {file}")
        continue

    codepoint = ord(name)

    glyph = font.createChar(codepoint)

    path = os.path.join(LETTER_DIR, file)
    glyph.importOutlines(path)

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0

    glyph.autoTrace()

    glyph.removeOverlap()

    glyph.simplify()

    glyph.round()

    glyph.width = 1000

    print(f"{name} U+{codepoint:04X}")

font.generate(OUTPUT)

print("Done")

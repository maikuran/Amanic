import os
import fontforge

LETTER_DIR = "Letter"
OUTPUT_FONT = "MyFont.ttf"

font = fontforge.font()

font.fontname = "MyFont"
font.familyname = "MyFont"
font.fullname = "MyFont"

font.encoding = "UnicodeFull"

font.em = 1000
font.ascent = 800
font.descent = 200

for filename in sorted(os.listdir(LETTER_DIR)):
    if not filename.lower().endswith(".png"):
        continue

    char = os.path.splitext(filename)[0]

    if len(char) != 1:
        print(f"Skip: {filename}")
        continue

    codepoint = ord(char)

    glyph = font.createChar(codepoint)

    png = os.path.join(LETTER_DIR, filename)

    glyph.importOutlines(png)
    glyph.autoTrace()
    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.round()
    glyph.simplify()

    glyph.left_side_bearing = 0
    glyph.right_side_bearing = 0
    glyph.width = 1000

    print(f"Added {char} U+{codepoint:04X}")

font.generate(OUTPUT_FONT)

print("Finished.")

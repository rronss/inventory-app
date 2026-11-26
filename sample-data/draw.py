"""Draws the pictures of the sample items. Needs Pillow:  pip install pillow && python sample-data/draw.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
SIZE = (1600, 1200)  # drawn at twice the size, then reduced for smooth edges
DARK, MID, LIGHT, ACCENT = "#1b1f2a", "#3a4050", "#c9ced8", "#6f57e8"


def canvas(shadow_box):
    image = Image.new("RGB", SIZE, "white")
    shadow = Image.new("L", SIZE, 0)
    ImageDraw.Draw(shadow).ellipse(shadow_box, fill=70)
    image.paste("#9aa1ad", mask=shadow.filter(ImageFilter.GaussianBlur(28)))
    return image, ImageDraw.Draw(image)


def save(image, name):
    image.resize((800, 600), Image.LANCZOS).save(HERE / name, optimize=True)


def monitor():
    image, draw = canvas((430, 990, 1170, 1060))
    draw.rounded_rectangle((250, 160, 1350, 820), radius=28, fill=DARK)
    for row in range(610):  # the screen: a soft gradient
        t = row / 610
        colour = (int(46 + 90 * t), int(62 + 20 * t), int(150 + 60 * t))
        draw.line((276, 186 + row, 1324, 186 + row), fill=colour)
    draw.polygon([(276, 796), (640, 470), (900, 700), (1060, 560), (1324, 796)], fill="#2a2f63")
    draw.ellipse((1080, 260, 1190, 370), fill="#f4d58d")
    draw.polygon([(740, 820), (860, 820), (885, 990), (715, 990)], fill=MID)
    draw.rounded_rectangle((560, 975, 1040, 1025), radius=22, fill=DARK)
    save(image, "monitor.png")


def keyboard():
    image, draw = canvas((180, 800, 1420, 900))
    draw.rounded_rectangle((150, 360, 1450, 840), radius=46, fill=DARK)
    rows = [[1] * 13 + [1.9], [1.5] + [1] * 12 + [1.4], [1.8] + [1] * 11 + [2.1], [2.35] + [1] * 10 + [2.55],
            [1.3, 1.3, 1.3, 6.2, 1.3, 1.3, 1.3, 0.9]]
    for line, widths in enumerate(rows):
        gap, left, top = 12, 188, 394 + line * 84
        unit = (1224 - gap * (len(widths) - 1)) / sum(widths)
        for position, width in enumerate(widths):
            right = left + width * unit
            colour = ACCENT if (line, position) in {(0, 0), (2, len(widths) - 1)} else "#f2f3f6"
            draw.rounded_rectangle((left, top, right, top + 70), radius=12, fill=colour)
            draw.rounded_rectangle((left + 7, top + 6, right - 7, top + 54), radius=8, outline=LIGHT, width=2)
            left = right + gap
    save(image, "keyboard.png")


def cable():
    image, draw = canvas((300, 930, 1300, 1010))
    for box, start, end in [((420, 300, 1180, 900), 0, 360), ((500, 370, 1100, 830), 0, 360),
                            ((460, 330, 1140, 870), 140, 400)]:
        draw.arc(box, start, end, fill=DARK, width=34)
    draw.line((470, 760, 330, 930), fill=DARK, width=34)
    draw.line((1130, 440, 1270, 270), fill=DARK, width=34)
    for (x, y), direction in [((330, 930), (-1, 1)), ((1270, 270), (1, -1))]:
        dx, dy = direction[0] * 0.64, direction[1] * 0.768  # along the end of the cable
        draw.line((x, y, x + dx * 130, y + dy * 130), fill=MID, width=82)
        draw.line((x + dx * 130, y + dy * 130, x + dx * 195, y + dy * 195), fill=LIGHT, width=54)
    save(image, "cable.png")


def monitor_back():
    image, draw = canvas((430, 990, 1170, 1060))
    draw.rounded_rectangle((250, 160, 1350, 820), radius=40, fill=MID)
    for y in range(200, 330, 26):  # vents
        draw.rounded_rectangle((520, y, 1080, y + 8), radius=4, fill=DARK)
    draw.rounded_rectangle((660, 420, 940, 700), radius=36, fill=DARK)  # stand mount
    draw.polygon([(750, 560), (850, 560), (885, 990), (715, 990)], fill="#252a37")
    draw.rounded_rectangle((560, 975, 1040, 1025), radius=22, fill=DARK)
    draw.rounded_rectangle((340, 700, 600, 760), radius=14, fill=DARK)  # ports
    for x, width in [(362, 70), (452, 58), (530, 46)]:
        draw.rounded_rectangle((x, 716, x + width, 744), radius=6, fill=LIGHT)
    save(image, "monitor-back.png")


def keyboard_close():
    image, draw = canvas((200, 900, 1400, 1010))
    draw.rounded_rectangle((90, 250, 1510, 930), radius=60, fill=DARK)
    font = ImageFont.load_default(size=96)
    for line, (letters, left) in enumerate([("QWER", 170), ("ASDF", 250)]):
        for position, letter in enumerate(letters):
            x, y = left + position * 300, 330 + line * 280
            colour = ACCENT if letter == "F" else "#f2f3f6"
            draw.rounded_rectangle((x, y, x + 260, y + 240), radius=34, fill=colour)
            draw.rounded_rectangle((x + 24, y + 18, x + 236, y + 196), radius=24, outline=LIGHT, width=5)
            draw.text((x + 56, y + 40), letter, font=font, fill="white" if letter == "F" else DARK)
    save(image, "keyboard-close.png")


def cable_plug():
    image, draw = canvas((300, 860, 1300, 960))
    draw.rounded_rectangle((0, 540, 640, 660), radius=20, fill=DARK)  # the cable
    for x in range(30, 600, 42):  # braiding
        draw.line((x, 548, x + 56, 652), fill=MID, width=10)
    draw.rounded_rectangle((590, 450, 1060, 750), radius=70, fill=MID)  # the grip
    draw.rounded_rectangle((1040, 500, 1380, 700), radius=95, fill=LIGHT)  # the metal plug
    draw.rounded_rectangle((1090, 548, 1330, 652), radius=52, fill="#8b92a1")
    draw.rounded_rectangle((1120, 586, 1300, 614), radius=12, fill=DARK)
    save(image, "cable-plug.png")


if __name__ == "__main__":
    for picture in (monitor, monitor_back, keyboard, keyboard_close, cable, cable_plug):
        picture()
    print("wrote the sample pictures")

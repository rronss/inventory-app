"""Draws the default avatars people can pick. Needs Pillow:  pip install pillow && python frontend/draw_avatars.py

Illustrations, not likenesses of anyone.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "public" / "avatars"
S = 1200  # drawn large, then reduced for smooth edges
DARK = "#1b1f2a"


def start(ring, background, clothes, skin):
    image = Image.new("RGB", (S, S), ring)
    draw = ImageDraw.Draw(image)
    draw.ellipse((120, 120, 1080, 1080), fill=background)
    draw.rounded_rectangle((260, 830, 940, 1300), radius=230, fill=clothes)
    draw.rounded_rectangle((528, 700, 672, 880), radius=60, fill=skin)  # neck
    return image, draw


def face(draw, skin):
    draw.ellipse((340, 280, 860, 820), fill=skin)
    draw.ellipse((305, 510, 390, 625), fill=skin)  # ears
    draw.ellipse((810, 510, 895, 625), fill=skin)
    for x in (480, 720):  # eyes
        draw.ellipse((x - 28, 552, x + 28, 608), fill=DARK)
        draw.ellipse((x - 6, 562, x + 12, 580), fill="white")
    draw.arc((505, 600, 695, 740), 30, 150, fill=DARK, width=18)  # smile


def cap():
    skin = "#e9ae83"
    image, draw = start("#2b3157", "#6f57e8", DARK, skin)
    face(draw, skin)
    draw.pieslice((330, 230, 870, 710), 180, 360, fill="#f4b63f")
    draw.rounded_rectangle((300, 440, 900, 505), radius=32, fill="#d99a24")
    draw.ellipse((572, 205, 628, 261), fill="#d99a24")
    return image


def short_hair():
    skin = "#8d5a3b"
    image, draw = start("#0f4c45", "#2fae9b", "#f2f4f7", skin)
    face(draw, skin)
    draw.chord((335, 250, 865, 690), 180, 360, fill="#1d1410")
    return image


def long_hair():
    skin = "#f3c7a6"
    hair = "#7a3b1d"
    image, draw = start("#8a2f2a", "#f0705f", "#2b3157", skin)
    draw.rounded_rectangle((295, 240, 905, 940), radius=300, fill=hair)  # behind the face
    draw.rounded_rectangle((528, 700, 672, 880), radius=60, fill=skin)
    face(draw, skin)
    draw.chord((335, 258, 865, 600), 180, 360, fill=hair)  # fringe
    return image


def hard_hat():
    skin = "#c68a5e"
    image, draw = start("#123a63", "#3b8bd8", "#f97316", skin)
    face(draw, skin)
    draw.pieslice((320, 200, 880, 760), 180, 360, fill="#facc15")
    draw.rounded_rectangle((565, 190, 635, 470), radius=30, fill="#eab308")
    draw.rounded_rectangle((270, 450, 930, 515), radius=32, fill="#eab308")
    for x in (480, 720):  # glasses
        draw.ellipse((x - 72, 508, x + 72, 652), outline=DARK, width=16)
    draw.line((552, 575, 648, 575), fill=DARK, width=16)
    return image


def bun():
    skin = "#e0a97e"
    hair = "#2a2233"
    image, draw = start("#2f5d27", "#6dbb55", "#6f57e8", skin)
    draw.ellipse((500, 150, 700, 350), fill=hair)
    face(draw, skin)
    draw.chord((330, 250, 870, 640), 180, 360, fill=hair)
    for x in (345, 855):  # earrings
        draw.ellipse((x - 22, 618, x + 22, 662), fill="#f4d58d")
    return image


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for number, drawing in enumerate([cap, short_hair, long_hair, hard_hat, bun], start=1):
        drawing().resize((400, 400), Image.LANCZOS).save(OUT / f"{number}.png", optimize=True)
        print(f"avatars/{number}.png")

"""
Pixel-art Spider-Man Noir sprite generator.
Generates 16x16 pixel-art scaled 3x with NEAREST -> 48x48 per frame.
Features 1930s fedora, billowing trench coat, stitched mask with glowing white circular goggles,
Rubik's cube interaction, and web-shooting attacks.
"""

from pathlib import Path
from PIL import Image

OUT = Path(__file__).parent / "sprites" / "spider_noir"
OUT.mkdir(parents=True, exist_ok=True)

SRC = 16
SCALE = 3

# ── Spider-Man Noir Palette ────────────────────────────────────────────────────
P: dict[str, tuple] = {
    ".": (0, 0, 0, 0),             # Transparent
    "K": (10, 11, 14, 255),         # Deep outline / shadow
    "H": (32, 34, 40, 255),         # Fedora Crown mid
    "h": (22, 23, 27, 255),         # Fedora Crown dark
    "D": (15, 16, 19, 255),         # Fedora Brim dark
    "B": (54, 57, 68, 255),         # Fedora Hat Band
    "M": (30, 32, 38, 255),         # Mask fabric
    "m": (20, 21, 26, 255),         # Mask shadow / seam
    "G": (14, 15, 18, 255),         # Goggle rim / frame
    "W": (255, 255, 255, 255),     # Goggle bright white lens
    "w": (210, 230, 245, 255),     # Goggle sheen / soft blue-white
    "C": (42, 45, 54, 255),         # Trench coat mid
    "c": (28, 30, 36, 255),         # Trench coat dark / folds
    "L": (72, 77, 92, 255),         # Trench coat highlight / edge light
    "S": (56, 60, 72, 255),         # Turtleneck / collar
    "T": (22, 24, 29, 255),         # Vest / Gun holster straps
    "t": (185, 195, 210, 255),     # Metallic button / clasp
    "g": (25, 27, 33, 255),         # Leather gloves
    "P": (24, 26, 31, 255),         # Trousers
    "b": (14, 15, 18, 255),         # Detective boots
    # Rubik's cube & special effects
    "R": (215, 42, 42, 255),        # Red cube face
    "Y": (240, 205, 40, 255),       # Yellow cube face
    "U": (40, 100, 220, 255),       # Blue cube face
    "E": (40, 185, 75, 255),        # Green cube face
    "O": (240, 125, 30, 255),       # Orange cube face
    "I": (245, 245, 245, 255),      # White cube face
    "X": (245, 250, 255, 250),      # Web line bright
    "x": (190, 210, 235, 190),      # Web line sheen
    "z": (160, 180, 215, 200),      # Zzz
}


def px_img(rows: list[str]) -> Image.Image:
    """Build 16x16 image from rows, scale 3x nearest."""
    img = Image.new("RGBA", (SRC, SRC), (0, 0, 0, 0))
    for y, row in enumerate(rows[:SRC]):
        for x, ch in enumerate(row[:SRC]):
            color = P.get(ch, P["."])
            img.putpixel((x, y), color)
    return img.resize((SRC * SCALE, SRC * SCALE), Image.NEAREST)


def sheet(frames: list[Image.Image]) -> Image.Image:
    if not frames:
        return Image.new("RGBA", (SRC * SCALE, SRC * SCALE))
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


def mirror(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


# ── IDLE ANIMATION ────────────────────────────────────────────────────────────
# Stance: Fedora brim tilted forward, glowing white goggles, high collar,
# trench coat fluttering subtly in the noir wind.

IDLE_A = [
    "....hhhhhh......",   # Fedora crown
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",   # Hat band
    "..DDDDDDDDDD....",   # Fedora brim
    "....MMMMMM......",   # Head / Mask
    "...MGWWGGWWGM...",   # Goggles glowing white
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",   # High popped collar + stitched mask
    "..LCcTTttTTcCL..",   # Shoulders, holster straps, vest buttons
    "..CCcTTTTTTcCC..",   # Torso / coat
    "..CCcCCCCCC.C...",   # Trench coat flare
    "..CCcCCCCCC.CL..",   # Wind catches coat back (col 12-13)
    "...PPP....PPP...",   # Dark trousers
    "...PPP....PPP...",
    "...bbb....bbb...",   # Detective boots
    "................",
]

IDLE_B = [   # Wind flutters coat back + subtle detective breathing bob
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CL..",
    "..CCcCCCCCC..CL.",   # Coat flap waves out
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]

IDLE_C = [   # Breathing down 1 row
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]

IDLE_BLINK = [   # Goggles narrow into focused squint / slits
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGGGGGGGGGM..",
    "...MGWWGGWWGM...",   # Thin squinted eyes
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.C...",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]


# ── WALK CYCLE (Facing Right) ─────────────────────────────────────────────────
# 4 frames: Stride forward, coat tails trailing behind him in the wind.

WALK_R0 = [  # Left foot forward, right foot back, coat trailing
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCCC.",
    "..CCcCCCCCC.CCL.",   # Coat tails flowing back
    "...PPP...PPP.CL.",
    "..PPP.....PPP...",
    "..bbb......bbb..",
    "................",
    "................",
]

WALK_R1 = [  # Passing step (bob up)
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CL..",
    "...PPP...PPP....",
    "...PPP...PPP....",
    "...bbb...bbb....",
    "................",
]

WALK_R2 = [  # Right foot forward, left foot back, coat whip
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCCCC",
    "..CCcCCCCCC..CCL",   # Wider coat flutter
    "....PPP...PPP.CL",
    "...PPP.....PPP..",
    "...bbb......bbb.",
    "................",
    "................",
]

WALK_R3 = [  # Mid-step recovery
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]

WALK_R = [WALK_R0, WALK_R1, WALK_R2, WALK_R3]


# ── SIT / PERCH (Gargoyle / Detective Rooftop Stance) ─────────────────────────
# Crouched low, coat draped over knee, brooding down at the city.

SIT_A = [
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MGWWG.m.CL.",   # Looking down slightly
    "..LCcTTttTTcCL..",
    "..CCCCCCCCCCCC..",   # Coat wraps around crouch
    ".CCcCCCCCCCCcCC.",
    ".CCcCCCCCCCCcCC.",
    "..PPb......bPP..",   # Tucked crouch boots
    "..bbb......bbb..",
    "................",
    "................",
]

SIT_B = [   # Subtle head tilt / coat shift during crouch
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGGGGGGGGGM..",   # Eyes blink while sitting
    "..LC.MGWWG.m.CL.",
    "..LCcTTttTTcCL..",
    "..CCCCCCCCCCCC..",
    ".CCcCCCCCCCCcCC.",
    ".CCcCCCCCCCCcCCL",
    "..PPb......bPP..",
    "..bbb......bbb..",
    "................",
    "................",
]


# ── SLEEP ─────────────────────────────────────────────────────────────────────
# Slumped brooding against the edge, fedora brim pulled down over goggles, "zzz"

SLEEP_A = [
    "................",
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh...z.",
    "..DDDDDDDDDD....",   # Brim pulled down concealing eyes
    "....MmMMmM......",
    "...MmMMMMmM.....",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CC..",
    ".CCcCCCCCCCCcCC.",
    ".PPbb......bbPP.",
    ".bbbb......bbbb.",
    "................",
    "................",
]

SLEEP_B = [
    "................",
    "..............z.",
    "....hhhhhh...z..",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MmMMmM......",
    "...MmMMMMmM.....",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CC..",
    ".CCcCCCCCCCCcCC.",
    ".PPbb......bbPP.",
    ".bbbb......bbbb.",
    "................",
    "................",
]

SLEEP_C = [
    ".............z..",
    "............z...",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MmMMmM......",
    "...MmMMMMmM.....",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CC..",
    ".CCcCCCCCCCCcCC.",
    ".PPbb......bbPP.",
    ".bbbb......bbbb.",
    "................",
    "................",
]


# ── WAKE ──────────────────────────────────────────────────────────────────────
# Reaches up, tips fedora brim up, goggles flare bright white!

WAKE_A = [   # Hand reaching up to brim
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDDg...",   # Gloved hand on brim
    "....MMMMMM..g...",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.C...",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]

WAKE_B = [   # Fedora tipped up slightly, eyes flash bright white
    "...hhhhhh.......",
    "..hHHHHHHh......",
    "..hBBBBBBh......",
    ".DDDDDDDDDD.g...",   # Tilted brim
    "...MMMMMM...g...",
    "..MGWWGGWWGM....",
    "..MGWWGGWWGM....",
    ".LC.MmMMmM.CL...",
    ".LCcTTttTTcCL...",
    ".CCcTTTTTTcCC...",
    ".CCcCCCCCC.C....",
    ".CCcCCCCCC.CL...",
    "..PPP....PPP....",
    "..PPP....PPP....",
    "..bbb....bbb....",
    "................",
]

WAKE_C = IDLE_A


# ── BLINK ─────────────────────────────────────────────────────────────────────
BLINK_A = IDLE_A
BLINK_B = IDLE_BLINK
BLINK_C = IDLE_BLINK
BLINK_D = IDLE_A


# ── HAPPY (Left-click): The Iconic Spider-Verse Rubik's Cube! ─────────────────
# Pulls out his Rubik's cube, inspects it, turns a side ("Is this purple?")!

HAPPY_A = [   # Pulls out Rubik's cube with gloved hands
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcRYUcCL.....",   # Holding cube in front
    "..CCcEIOcCC.....",
    "..CCcCCCCCC.C...",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]

HAPPY_B = [   # Twists cube face (colors rotate), head tilts in curiosity
    "...hhhhhh.......",   # Head curious tilt
    "..hHHHHHHh......",
    "..hBBBBBBh......",
    ".DDDDDDDDDD.....",
    "...MMMMMM.......",
    "..MGWWGGWWGM....",
    "..MGWWGGWWGM....",
    ".LC.MmMMmM.CL...",
    ".LCcgUIYgCL.....",   # Hands twisting cube
    ".CCc.ORE.CC.....",
    ".CCcCCCCCC.C....",
    ".CCcCCCCCC.CL...",
    "..PPP....PPP....",
    "..PPP....PPP....",
    "..bbb....bbb....",
    "................",
]

HAPPY_C = [   # Holds cube up high to the light ("Wherever I go...")
    "....hhhhhh..RY..",   # Cube held high
    "...hHHHHHHhgUI..",
    "...hBBBBBBh.g...",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",   # Looking up at it
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.C...",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]

HAPPY_D = [   # Satisfied nod with cube tucked away
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.C...",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
]


# ── ROAR / SPECIAL (Double-click): Hard-Boiled Web Shot (THWIP!) ──────────────
# Drops into a combat stance, shoots a web line forward with web splatter!

ROAR_A = [   # Drops into low combat stance, coat flaring back
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCLCC",   # Wind catches coat
    "..CCcTTTTTTcCCCC",
    "..CCcCCCCCC..CCL",
    "..gPP.....PPg...",   # Hands preparing to fire
    ".PPP.......PPP..",
    ".bbb.......bbb..",
    "................",
    "................",
]

ROAR_B = [   # THWIP! Web shoots from wrist across the screen!
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTgXXXX",   # Web blast firing right!
    "..CCcCCCCCCc.xXx",
    "..gPP.....PPg.x.",
    ".PPP.......PPP..",
    ".bbb.......bbb..",
    "................",
    "................",
]

ROAR_C = [   # Web expands and sticks, coat billowing
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCLCC",
    "..CCcTTTTTTg.XXX",
    "..CCcCCCCCCc..xx",
    "..gPP.....PPg...",
    ".PPP.......PPP..",
    ".bbb.......bbb..",
    "................",
    "................",
]

ROAR_D = [   # Pulls back with clenched fist
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CL..",
    "...PPP....PPP...",
    "...PPP....PPP...",
    "...bbb....bbb...",
    "................",
    "................",
]


# ── JUMP (Web Zip Leap) ───────────────────────────────────────────────────────
# Leaps into the air, arms out, coat flapping violently, landing smoothly.

JUMP_A = [   # Crouch before leap
    "................",
    "................",
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    "..LCcTTttTTcCL..",
    "..CCcTTTTTTcCC..",
    "..CCcCCCCCC.CC..",
    "..PPb......bPP..",
    "..bbb......bbb..",
    "................",
    "................",
]

JUMP_B = [   # Air leap - coat tails down, legs tucked
    "..X.............",   # Web line pulling upward!
    "..x.hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    ".gLCcTTttTTcLg..",   # Arms extended
    ".CCcTTTTTTcCC...",
    ".CCcCCCCCC.CC...",
    "..CCcCCCCcCC....",
    "...PP....PP.....",
    "...bb....bb.....",
    "................",
    "................",
]

JUMP_C = [   # Apex of leap
    "....hhhhhh......",
    "...hHHHHHHh.....",
    "...hBBBBBBh.....",
    "..DDDDDDDDDD....",
    "....MMMMMM......",
    "...MGWWGGWWGM...",
    "...MGWWGGWWGM...",
    "..LC.MmMMmM.CL..",
    ".gLCcTTttTTcLg..",
    ".CCcTTTTTTcCC...",
    ".CCcCCCCCC.CC...",
    "..CCcCCCCcCC....",
    "...PP....PP.....",
    "...bb....bb.....",
    "................",
    "................",
]

JUMP_D = IDLE_A


# ── Assemble Spider-Noir Animations ───────────────────────────────────────────
ANIMATIONS: dict[str, list[list[str]]] = {
    "idle":       [IDLE_A, IDLE_B, IDLE_A, IDLE_C, IDLE_A, IDLE_BLINK, IDLE_B, IDLE_A],
    "idle_flip":  [mirror(f) for f in [IDLE_A, IDLE_B, IDLE_A, IDLE_C, IDLE_A, IDLE_BLINK, IDLE_B, IDLE_A]],
    "walk_right": WALK_R,
    "walk_left":  [mirror(f) for f in WALK_R],
    "sit":        [SIT_A, SIT_A, SIT_B, SIT_A],
    "sleep":      [SLEEP_A, SLEEP_B, SLEEP_C, SLEEP_B],
    "wake":       [WAKE_A, WAKE_B, WAKE_B, WAKE_C],
    "blink":      [BLINK_A, BLINK_B, BLINK_C, BLINK_D],
    "happy":      [HAPPY_A, HAPPY_B, HAPPY_C, HAPPY_D],
    "roar":       [ROAR_A, ROAR_B, ROAR_C, ROAR_D],
    "jump":       [JUMP_A, JUMP_B, JUMP_C, JUMP_D],
}


def generate_all(target_dir: Path | None = None):
    out_dir = target_dir or OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating Spider-Man Noir sprites in {out_dir}...")
    for name, frames in ANIMATIONS.items():
        images = [px_img(f) for f in frames]
        sht = sheet(images)
        path = out_dir / f"{name}.png"
        sht.save(path)
        print(f"  OK {name}.png ({len(frames)} frames, {sht.width}x{sht.height}px)")
    print("Spider-Man Noir sprites generated successfully.")


if __name__ == "__main__":
    generate_all()

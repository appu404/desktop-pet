"""
HD Sprite Generator for Chibi Spider-Man Noir.
Generates 256x256 high-resolution, smooth frames using authentic hand-drawn
Spider-Noir action frames:
- 10-frame smooth detective walk cycle (walk_right / walk_left)
- Hardboiled standing idle with coat flutter and lens glimmer (idle / idle_flip)
- Detective squint & focus (blink)
- Private eye case notes on wooden crate with animated pencil & notebook (investigate)
- Relaxed rooftop perch sitting on the floor (sit)
- Fedora pulled low with floating comic Zzz slumber (sleep)
- Alert wake-up with dual lens sparkles (wake)
- The iconic Rubik's cube interaction with vibrant color facets & sparkles (happy)
- Police dispatch radio call turning into hilarious web backfire mishap (roar)
- Dynamic web-zip leap and superhero landing (jump)
"""

from pathlib import Path
import math
import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw, ImageFilter

SOURCE_DIR = Path(__file__).parent / "source"
SOURCE_IMAGE = SOURCE_DIR / "spider_noir_actions.jpg"
FALLING_IMAGE = SOURCE_DIR / "spider_noir_falling.jpg"
CLIMB_IMAGE = SOURCE_DIR / "spider_noir_climb.jpg"
OUT_DIR = Path(__file__).parent / "sprites" / "spider_noir"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_SIZE = 256
SCALE = 1.6
GROUND_Y = 244


def extract_climb_sprites(src_path: Path) -> dict[str, Image.Image]:
    if not src_path.exists():
        return {}
    im = Image.open(src_path).convert("RGB")
    arr = np.array(im).astype(np.float32)

    dist_to_white = np.linalg.norm(arr - 255.0, axis=2)
    is_dark = dist_to_white >= 25.0
    lbl, _ = ndi.label(is_dark)

    coords = [
        ("climb_01", 110, 250),
        ("climb_02", 270, 250),
        ("climb_03", 440, 260),
        ("climb_04", 620, 310),
        ("climb_05", 780, 260),
        ("climb_06", 930, 300),
    ]

    climb_raw = {}
    for name, cx, cy in coords:
        if cy >= lbl.shape[0] or cx >= lbl.shape[1]:
            continue
        label_id = lbl[cy, cx]
        mask = (lbl == label_id)
        mask_filled = ndi.binary_fill_holes(mask)

        ys, xs = np.where(mask_filled)
        if len(ys) == 0:
            continue
        y1, y2 = max(0, ys.min() - 4), min(arr.shape[0], ys.max() + 5)
        x1, x2 = max(0, xs.min() - 4), min(arr.shape[1], xs.max() + 5)

        sub_rgb = arr[y1:y2, x1:x2].copy()
        sub_filled = mask_filled[y1:y2, x1:x2]
        sub_dilated = ndi.binary_dilation(sub_filled, iterations=2)

        alpha = np.zeros(sub_filled.shape, dtype=np.float32)
        alpha[sub_filled] = 1.0

        sub_dist = dist_to_white[y1:y2, x1:x2]
        edge = sub_dilated & ~sub_filled
        alpha[edge] = np.clip(sub_dist[edge] / 30.0, 0.0, 1.0)

        rgb_clean = np.zeros_like(sub_rgb)
        for c in range(3):
            unblended = np.where(alpha > 0.02, (sub_rgb[:, :, c] - (1.0 - alpha) * 255.0) / np.maximum(alpha, 0.02), 0.0)
            rgb_clean[:, :, c] = np.clip(unblended, 0.0, 255.0)

        rgba = np.dstack([rgb_clean, alpha * 255.0]).astype(np.uint8)
        climb_raw[name] = Image.fromarray(rgba, "RGBA")

    return climb_raw


def extract_falling_sprites(src_path: Path) -> dict[str, Image.Image]:
    if not src_path.exists():
        return {}
    im = Image.open(src_path).convert("RGB")
    arr = np.array(im).astype(np.float32)

    dist_to_white = np.linalg.norm(arr - 255.0, axis=2)
    is_dark = dist_to_white >= 25.0
    lbl, _ = ndi.label(is_dark)

    parts = [
        ("fall_01", [(60, 100), (100, 200)]),   # hat + body
        ("fall_02", [(300, 200)]),
        ("fall_03", [(450, 280)]),
        ("fall_04", [(600, 350)]),
        ("fall_05", [(790, 260), (760, 360)]),   # hat + body
        ("fall_06", [(900, 430)]),
    ]

    extracted = {}
    for name, pt_list in parts:
        label_ids = [lbl[y, x] for x, y in pt_list if y < lbl.shape[0] and x < lbl.shape[1]]
        mask = np.isin(lbl, label_ids)
        mask_filled = ndi.binary_fill_holes(mask)

        ys, xs = np.where(mask_filled)
        if len(ys) == 0:
            continue
        y1, y2 = max(0, ys.min() - 4), min(arr.shape[0], ys.max() + 5)
        x1, x2 = max(0, xs.min() - 4), min(arr.shape[1], xs.max() + 5)

        sub_rgb = arr[y1:y2, x1:x2].copy()
        sub_filled = mask_filled[y1:y2, x1:x2]
        sub_dilated = ndi.binary_dilation(sub_filled, iterations=2)

        alpha = np.zeros(sub_filled.shape, dtype=np.float32)
        alpha[sub_filled] = 1.0

        sub_dist = dist_to_white[y1:y2, x1:x2]
        edge = sub_dilated & ~sub_filled
        alpha[edge] = np.clip(sub_dist[edge] / 30.0, 0.0, 1.0)

        rgb_clean = np.zeros_like(sub_rgb)
        for c in range(3):
            unblended = np.where(alpha > 0.02, (sub_rgb[:, :, c] - (1.0 - alpha) * 255.0) / np.maximum(alpha, 0.02), 0.0)
            rgb_clean[:, :, c] = np.clip(unblended, 0.0, 255.0)

        rgba = np.dstack([rgb_clean, alpha * 255.0]).astype(np.uint8)
        extracted[name] = Image.fromarray(rgba, "RGBA")

    return extracted


def make_canvas() -> Image.Image:
    return Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))


def sheet(frames: list[Image.Image]) -> Image.Image:
    if not frames:
        return make_canvas()
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


def draw_glow(canvas: Image.Image, center: tuple[int, int], radius: int, color=(255, 255, 255, 120)):
    glow = Image.new("RGBA", (radius * 4, radius * 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    cx, cy = radius * 2, radius * 2
    for r in range(radius, 0, -2):
        alpha = int(color[3] * (1.0 - r / radius))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(color[0], color[1], color[2], alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(max(1, radius // 3)))
    canvas.paste(glow, (center[0] - cx, center[1] - cy), glow)


def draw_cross_sparkle(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color=(255, 255, 255, 255)):
    draw.line([x - size, y, x + size, y], fill=color, width=2)
    draw.line([x, y - size, x, y + size], fill=color, width=2)
    s2 = max(1, size // 2)
    draw.line([x - s2, y - s2, x + s2, y + s2], fill=color, width=1)
    draw.line([x - s2, y + s2, x + s2, y - s2], fill=color, width=1)


def extract_raw_sprites(src_path: Path) -> dict[str, Image.Image]:
    im = Image.open(src_path).convert("RGB")
    arr = np.array(im).astype(np.float32)

    sprite_defs = [
        ("walk_01", 0, 128, 20, 92),
        ("walk_02", 0, 128, 128, 194),
        ("walk_03", 0, 128, 222, 287),
        ("walk_04", 0, 128, 318, 387),
        ("walk_05", 0, 128, 422, 493),
        ("walk_06", 0, 128, 528, 598),
        ("walk_07", 0, 128, 634, 699),
        ("walk_08", 0, 128, 729, 798),
        ("walk_09", 0, 128, 827, 894),
        ("walk_10", 0, 128, 931, 1000),
        ("pose_notes", 128, 256, 15, 110),
        ("pose_sit_side", 128, 256, 280, 390),
        ("pose_sit_front", 128, 256, 400, 515),
        ("pose_rubik", 128, 256, 515, 632),
        ("pose_radio", 128, 256, 642, 755),
        ("pose_radio_web", 128, 256, 910, 1018),
    ]

    extracted = {}
    for name, y1, y2, x1, x2 in sprite_defs:
        sub = arr[y1:y2, x1:x2].copy()
        h, w, _ = sub.shape

        diff = np.linalg.norm(sub - 247.0, axis=2)
        bg_candidate = diff < 16.0

        lbl, _ = ndi.label(bg_candidate)
        border_mask = np.zeros((h, w), dtype=bool)
        border_mask[0, :] = True
        border_mask[-1, :] = True
        border_mask[:, 0] = True
        border_mask[:, -1] = True

        border_labels = set(lbl[border_mask]) - {0}
        outer_bg = np.isin(lbl, list(border_labels))

        if name == "pose_notes":
            # Protect the white notepad paper from background flood
            notepad_mask = np.zeros((h, w), dtype=bool)
            notepad_mask[40:65, 48:76] = True
            outer_bg = outer_bg & ~notepad_mask

        alpha = np.ones((h, w), dtype=np.float32)
        alpha[outer_bg] = 0.0

        # Anti-aliasing at the transition edge
        edge = ndi.binary_dilation(outer_bg, iterations=1) & ~outer_bg
        edge_brightness = np.mean(sub, axis=2)
        alpha[edge] = np.clip((247.0 - edge_brightness[edge]) / (247.0 - 50.0), 0.0, 1.0)

        # Unblend edge with background color (247, 247, 247)
        rgb_clean = np.zeros_like(sub)
        for c in range(3):
            unblended = np.where(alpha > 0.05, (sub[:, :, c] - (1.0 - alpha) * 247.0) / np.maximum(alpha, 0.05), 0.0)
            rgb_clean[:, :, c] = np.clip(unblended, 0.0, 255.0)

        rgba = np.dstack([rgb_clean, alpha * 255.0]).astype(np.uint8)
        extracted[name] = Image.fromarray(rgba, "RGBA")

    return extracted


def place_sprite(sprite: Image.Image,
                 target_canvas: Image.Image,
                 offset_x: int = 0,
                 offset_y: int = 0,
                 scale: float = SCALE,
                 custom_center_x: float | None = None) -> Image.Image:
    arr = np.array(sprite)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 40)
    if len(ys) == 0:
        return target_canvas

    y_max = ys.max()
    x_center = (xs.min() + xs.max()) / 2.0 if custom_center_x is None else custom_center_x

    new_w = max(1, int(round(sprite.width * scale)))
    new_h = max(1, int(round(sprite.height * scale)))
    scaled = sprite.resize((new_w, new_h), Image.Resampling.LANCZOS)

    pos_x = int(round(CANVAS_SIZE / 2.0 - x_center * scale)) + offset_x
    pos_y = int(round(GROUND_Y - y_max * scale)) + offset_y

    target_canvas.paste(scaled, (pos_x, pos_y), scaled)
    return target_canvas


def generate_all():
    print(f"Loading source sheet: {SOURCE_IMAGE}")
    raw = extract_raw_sprites(SOURCE_IMAGE)

    # ── 1. WALK RIGHT (10-frame authentic walk cycle) ─────────────────────────
    walk_right_frames = []
    for i in range(1, 11):
        name = f"walk_{i:02d}"
        c = make_canvas()
        place_sprite(raw[name], c)
        walk_right_frames.append(c)

    # ── 2. WALK LEFT (Flipped) ────────────────────────────────────────────────
    walk_left_frames = [f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in walk_right_frames]

    # ── 3. IDLE (Standing detective breathing with eye gleam) ─────────────────
    idle_frames = []
    base_stand = raw["walk_02"]
    bobs = [0, -1, -2, -2, -1, 0]
    for i, bob in enumerate(bobs):
        c = make_canvas()
        place_sprite(base_stand, c, offset_y=bob)
        # Goggle sheen pulse on peak breathing frames
        if i in (2, 3):
            # Eye center roughly around (135, 102)
            draw_glow(c, (134, 102 + bob), 10, (255, 255, 255, 80))
            d = ImageDraw.Draw(c)
            draw_cross_sparkle(d, 134, 102 + bob, 5, (255, 255, 255, 200))
        idle_frames.append(c)

    # ── 4. IDLE_FLIP (Flipped) ────────────────────────────────────────────────
    idle_flip_frames = [f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in idle_frames]

    # ── 5. BLINK (Detective Squint & Focus) ───────────────────────────────────
    blink_frames = []
    # Frame 0: Open eyes
    b0 = make_canvas()
    place_sprite(base_stand, b0)
    blink_frames.append(b0)

    # Frame 1: Half squint
    b1 = make_canvas()
    place_sprite(base_stand, b1)
    bd1 = ImageDraw.Draw(b1)
    # Mask eye slit
    bd1.rectangle([123, 98, 145, 102], fill=(24, 25, 28, 255))
    blink_frames.append(b1)

    # Frame 2: Deep focused slit
    b2 = make_canvas()
    place_sprite(base_stand, b2)
    bd2 = ImageDraw.Draw(b2)
    bd2.rectangle([123, 97, 145, 104], fill=(24, 25, 28, 255))
    blink_frames.append(b2)

    # Frame 3: Reopen with keen sparkle
    b3 = make_canvas()
    place_sprite(base_stand, b3)
    d3 = ImageDraw.Draw(b3)
    draw_cross_sparkle(d3, 138, 103, 7, (255, 255, 255, 240))
    blink_frames.append(b3)

    # ── 6. INVESTIGATE (Writing Case Notes on Wooden Crate) ───────────────────
    notes_raw = raw["pose_notes"]
    investigate_frames = []
    # 6 frames: pencil scribbling, observing scene, writing notes
    p_bobs = [0, 0, 0, -2, -2, 0]
    for i, bob in enumerate(p_bobs):
        c = make_canvas()
        place_sprite(notes_raw, c, offset_y=bob)
        d = ImageDraw.Draw(c)
        # Pencil scribble strokes on notebook page
        if i in (1, 2):
            d.line([145, 185 + bob, 153, 186 + bob], fill=(50, 50, 55, 220), width=2)
            d.line([146, 189 + bob, 155, 190 + bob], fill=(50, 50, 55, 220), width=2)
        elif i in (3, 4):
            # Head raised slightly, looking out into the room
            draw_cross_sparkle(d, 132, 102 + bob, 6, (255, 255, 255, 220))
        elif i == 5:
            d.line([145, 185, 156, 186], fill=(50, 50, 55, 220), width=2)
            d.line([146, 189, 158, 190], fill=(50, 50, 55, 220), width=2)
            d.line([145, 193, 152, 194], fill=(50, 50, 55, 220), width=2)
        investigate_frames.append(c)

    # ── 7. SIT (Relaxed Perch on Floor) ───────────────────────────────────────
    sit_side = raw["pose_sit_side"]
    sit_front = raw["pose_sit_front"]
    sit_frames = []
    # Frame 0-1: Sitting side resting
    for bob in [0, -1]:
        c = make_canvas()
        place_sprite(sit_side, c, offset_y=bob)
        sit_frames.append(c)
    # Frame 2-3: Glancing forward
    for bob in [-1, 0]:
        c = make_canvas()
        place_sprite(sit_front, c, offset_y=bob)
        sit_frames.append(c)

    # ── 8. SLEEP (Slumped with Fedora Down & Comic Zzz) ───────────────────────
    sleep_frames = []
    sleep_base = raw["pose_sit_front"].copy()
    # Darken goggles into deep shadow
    s_arr = np.array(sleep_base)
    white_mask = (s_arr[:, :, 0] > 180) & (s_arr[:, :, 1] > 180) & (s_arr[:, :, 2] > 180)
    s_arr[white_mask, 0] = 26
    s_arr[white_mask, 1] = 26
    s_arr[white_mask, 2] = 30
    sleep_dark = Image.fromarray(s_arr, "RGBA")

    z_patterns = [
        [(150, 75, 14, 180)],
        [(152, 68, 14, 210), (168, 52, 18, 150)],
        [(154, 60, 14, 230), (170, 44, 18, 190), (188, 28, 24, 130)],
        [(172, 38, 18, 180), (192, 22, 24, 160)],
        [(150, 78, 14, 160), (194, 18, 24, 140)],
        [(150, 74, 14, 190)],
    ]
    for i in range(6):
        c = make_canvas()
        bob = int(round(1.5 * math.sin(i * math.pi / 3.0)))
        place_sprite(sleep_dark, c, offset_y=bob)
        d = ImageDraw.Draw(c)
        for zx, zy, sz, alpha in z_patterns[i]:
            d.text((zx, zy - bob), "Z", fill=(210, 225, 245, alpha))
        sleep_frames.append(c)

    # ── 9. WAKE (Fedora Tips Up, Goggles Flash Bright) ────────────────────────
    wake_frames = []
    # Frame 0: Slumped asleep
    w0 = make_canvas()
    place_sprite(sleep_dark, w0)
    wake_frames.append(w0)

    # Frame 1: Head lifts up
    w1 = make_canvas()
    place_sprite(sit_front, w1, offset_y=-2)
    wake_frames.append(w1)

    # Frame 2: Goggles ignite with bright lens flares
    w2 = make_canvas()
    place_sprite(sit_front, w2, offset_y=-1)
    draw_glow(w2, (120, 115), 18, (255, 255, 255, 180))
    draw_glow(w2, (148, 115), 18, (255, 255, 255, 180))
    wd2 = ImageDraw.Draw(w2)
    draw_cross_sparkle(wd2, 120, 115, 12, (255, 255, 255, 255))
    draw_cross_sparkle(wd2, 148, 115, 14, (255, 255, 255, 255))
    wake_frames.append(w2)

    # Frame 3: Alert upright ready
    w3 = make_canvas()
    place_sprite(base_stand, w3)
    wake_frames.append(w3)

    # ── 10. HAPPY (The Iconic Rubik's Cube Interaction!) ─────────────────────
    rubik_raw = raw["pose_rubik"]
    happy_frames = []
    # 8 frames: inspecting cube -> twisting -> vibrant sparkles -> admiring colors
    sparkle_sets = [
        [],
        [((148, 182), 6, (255, 60, 60, 200))],
        [((146, 178), 8, (255, 50, 50, 240)), ((164, 185), 7, (60, 160, 255, 240))],
        [((150, 175), 9, (255, 215, 40, 240)), ((168, 180), 8, (50, 210, 80, 240)), ((138, 188), 7, (255, 140, 40, 240))],
        [((145, 178), 8, (255, 50, 50, 240)), ((162, 172), 9, (255, 215, 40, 240))],
        [((152, 170), 10, (255, 255, 255, 250)), ((165, 178), 8, (60, 170, 255, 240))],
        [((150, 176), 7, (255, 215, 40, 220))],
        [],
    ]
    r_bobs = [0, 0, -2, -2, -1, -3, -2, 0]
    for i in range(8):
        c = make_canvas()
        bob = r_bobs[i]
        place_sprite(rubik_raw, c, offset_y=bob)
        d = ImageDraw.Draw(c)
        for (sx, sy), sz, col in sparkle_sets[i]:
            draw_cross_sparkle(d, sx, sy + bob, sz, col)
        # Eye shine when admiring
        if i in (4, 5):
            draw_glow(c, (132, 114 + bob), 10, (255, 255, 255, 120))
        happy_frames.append(c)

    # ── 11. ROAR / SPECIAL (Radio Dispatch & Comic Web Mishap!) ──────────────
    radio_raw = raw["pose_radio"]
    radio_web_raw = raw["pose_radio_web"]
    roar_frames = []

    # Frame 0: Noir pulls out radio and holds to ear
    r0 = make_canvas()
    place_sprite(radio_raw, r0)
    roar_frames.append(r0)

    # Frame 1: Radio crackle & broadcast waves from antenna
    r1 = make_canvas()
    place_sprite(radio_raw, r1, offset_y=-1)
    rd1 = ImageDraw.Draw(r1)
    # Radio arcs near antenna (~ x=118, y=140)
    rd1.arc([105, 128, 125, 148], 220, 320, fill=(255, 255, 255, 220), width=2)
    rd1.arc([98, 120, 132, 154], 220, 320, fill=(220, 240, 255, 180), width=2)
    rd1.text((70, 105), "STATIC...", fill=(240, 240, 255, 220))
    roar_frames.append(r1)

    # Frame 2: Noir talks into radio
    r2 = make_canvas()
    place_sprite(radio_raw, r2, offset_y=0)
    rd2 = ImageDraw.Draw(r2)
    rd2.text((60, 100), "NOIR HERE...", fill=(255, 255, 255, 240))
    roar_frames.append(r2)

    # Frame 3: Accidental web shot triggers straight up!
    r3 = make_canvas()
    place_sprite(radio_raw, r3, offset_y=1)
    rd3 = ImageDraw.Draw(r3)
    # Bright glowing web blast beam upward
    rd3.line([145, 180, 140, 105], fill=(255, 255, 255, 255), width=4)
    rd3.line([145, 180, 130, 95], fill=(220, 240, 255, 230), width=2)
    rd3.line([145, 180, 152, 95], fill=(220, 240, 255, 230), width=2)
    draw_glow(r3, (142, 120), 16, (255, 255, 255, 220))
    rd3.text((158, 85), "THWIP!", fill=(255, 255, 255, 255))
    roar_frames.append(r3)

    # Frame 4: SPLAT! Giant web impact covers face and goggles!
    r4 = make_canvas()
    place_sprite(radio_web_raw, r4, offset_y=2)
    draw_glow(r4, (138, 120), 22, (255, 255, 255, 200))
    rd4 = ImageDraw.Draw(r4)
    # Impact bursts
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        x1 = int(138 + 22 * math.cos(rad))
        y1 = int(120 + 22 * math.sin(rad))
        x2 = int(138 + 38 * math.cos(rad))
        y2 = int(120 + 38 * math.sin(rad))
        rd4.line([x1, y1, x2, y2], fill=(240, 248, 255, 230), width=2)
    rd4.text((150, 75), "SPLAT!", fill=(255, 255, 255, 255))
    roar_frames.append(r4)

    # Frame 5: Sits in shock with web all over face
    r5 = make_canvas()
    place_sprite(radio_web_raw, r5, offset_y=0)
    rd5 = ImageDraw.Draw(r5)
    rd5.text((155, 95), "...", fill=(230, 230, 240, 240))
    roar_frames.append(r5)

    # Frame 6: Dazed head tilt
    r6 = make_canvas()
    place_sprite(radio_web_raw, r6, offset_y=-1)
    rd6 = ImageDraw.Draw(r6)
    draw_cross_sparkle(rd6, 120, 80, 6, (255, 220, 60, 240))
    draw_cross_sparkle(rd6, 155, 85, 7, (255, 220, 60, 240))
    roar_frames.append(r6)

    # Frame 7: Shakes head dazed
    r7 = make_canvas()
    place_sprite(radio_web_raw, r7, offset_y=0)
    rd7 = ImageDraw.Draw(r7)
    draw_cross_sparkle(rd7, 136, 75, 8, (255, 220, 60, 250))
    roar_frames.append(r7)

    # ── 12. JUMP (Action Crouch -> Web Zip Leap -> Apex -> Superhero Landing) ──
    jump_frames = []
    # Frame 0: Action crouch
    j0 = make_canvas()
    place_sprite(sit_side, j0, offset_y=2)
    jump_frames.append(j0)

    # Frame 1: Leaping high with web zip line
    j1 = make_canvas()
    jd1 = ImageDraw.Draw(j1)
    # Upward web zip cable
    jd1.line([132, 0, 132, 60], fill=(255, 255, 255, 250), width=3)
    draw_glow(j1, (132, 60), 12, (255, 255, 255, 200))
    place_sprite(base_stand, j1, offset_y=-35)
    jump_frames.append(j1)

    # Frame 2: Mid-air floating apex
    j2 = make_canvas()
    place_sprite(base_stand, j2, offset_y=-45)
    jump_frames.append(j2)

    # Frame 3: Superhero landing crouch
    j3 = make_canvas()
    place_sprite(sit_side, j3, offset_y=1)
    draw_glow(j3, (128, GROUND_Y), 15, (255, 255, 255, 140))
    jump_frames.append(j3)

    # ── 13. FALLING, DRAG & LANDING ANIMATIONS ───────────────────────────────
    falling_raw = extract_falling_sprites(FALLING_IMAGE)
    fall_frames = []
    drag_frames = []
    land_frames = []

    def place_centered(sprite, offset_x=0, offset_y=0):
        c = make_canvas()
        arr = np.array(sprite)
        ys, xs = np.where(arr[:, :, 3] > 40)
        x_center = (xs.min() + xs.max()) / 2.0
        y_center = (ys.min() + ys.max()) / 2.0
        pos_x = int(round(128 - x_center)) + offset_x
        pos_y = int(round(128 - y_center)) + offset_y
        c.paste(sprite, (pos_x, pos_y), sprite)
        return c

    def place_grounded(sprite, offset_x=0, offset_y=0):
        c = make_canvas()
        arr = np.array(sprite)
        ys, xs = np.where(arr[:, :, 3] > 40)
        x_center = (xs.min() + xs.max()) / 2.0
        y_bottom = ys.max()
        pos_x = int(round(128 - x_center)) + offset_x
        pos_y = int(round(GROUND_Y - y_bottom)) + offset_y
        c.paste(sprite, (pos_x, pos_y), sprite)
        return c

    if falling_raw:
        fall_frames = [
            place_centered(falling_raw["fall_01"]),
            place_centered(falling_raw["fall_02"]),
            place_centered(falling_raw["fall_03"]),
            place_centered(falling_raw["fall_04"]),
            place_centered(falling_raw["fall_05"]),
        ]
        drag_frames = [
            place_centered(falling_raw["fall_01"], offset_y=0),
            place_centered(falling_raw["fall_01"], offset_y=-3),
        ]
        land_0 = place_grounded(falling_raw["fall_06"], offset_y=1)
        land_1 = place_grounded(falling_raw["fall_06"], offset_y=0)
        d1 = ImageDraw.Draw(land_1)
        d1.arc([40, 236, 85, 248], 180, 360, fill=(230, 230, 230, 200), width=2)
        d1.arc([165, 236, 210, 248], 180, 360, fill=(230, 230, 230, 200), width=2)
        d1.ellipse([50, 240, 60, 246], fill=(220, 220, 220, 160))
        d1.ellipse([190, 240, 200, 246], fill=(220, 220, 220, 160))

        land_2 = place_grounded(falling_raw["fall_06"], offset_y=-1)
        d2 = ImageDraw.Draw(land_2)
        d2.arc([30, 237, 95, 247], 180, 360, fill=(200, 200, 200, 120), width=2)
        d2.arc([155, 237, 220, 247], 180, 360, fill=(200, 200, 200, 120), width=2)

        land_3 = place_grounded(falling_raw["fall_06"], offset_y=0)
        land_frames = [land_0, land_1, land_2, land_3]

    # ── 14. WALL CLIMBING & PERCH ANIMATIONS ─────────────────────────────────
    climb_raw = extract_climb_sprites(CLIMB_IMAGE)
    climb_up_frames = []
    climb_up_flip_frames = []
    climb_down_frames = []
    climb_down_flip_frames = []
    climb_perch_frames = []
    climb_perch_flip_frames = []

    def place_climb(sprite, offset_x=0, offset_y=0, scale=0.80, wall_margin=24):
        w = max(1, int(round(sprite.width * scale)))
        h = max(1, int(round(sprite.height * scale)))
        scaled = sprite.resize((w, h), Image.Resampling.LANCZOS)
        arr = np.array(scaled)
        ys, xs = np.where(arr[:, :, 3] > 40)
        c = make_canvas()
        pos_x = wall_margin + offset_x
        pos_y = int(round(128 - (ys.min() + ys.max()) / 2.0)) + offset_y
        c.paste(scaled, (pos_x, pos_y), scaled)
        return c

    if climb_raw:
        climb_up_frames = [
            place_climb(climb_raw["climb_01"]),
            place_climb(climb_raw["climb_02"]),
            place_climb(climb_raw["climb_05"]),
            place_climb(climb_raw["climb_03"]),
        ]
        climb_up_flip_frames = [f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in climb_up_frames]

        c_perch_0 = place_climb(climb_raw["climb_04"], offset_y=0)
        c_perch_1 = place_climb(climb_raw["climb_04"], offset_y=-1)
        c_perch_2 = place_climb(climb_raw["climb_04"], offset_y=0)
        c_perch_3 = place_climb(climb_raw["climb_04"], offset_y=1)
        climb_perch_frames = [c_perch_0, c_perch_1, c_perch_2, c_perch_3]
        climb_perch_flip_frames = [f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in climb_perch_frames]

        # Climbing down animation same as climbing up
        climb_down_frames = [f.copy() for f in climb_up_frames]
        climb_down_flip_frames = [f.copy() for f in climb_up_flip_frames]

    # ── Save All Sheets ───────────────────────────────────────────────────────
    animations = {
        "walk_right":  walk_right_frames,
        "walk_left":   walk_left_frames,
        "idle":        idle_frames,
        "idle_flip":   idle_flip_frames,
        "blink":       blink_frames,
        "sit":         sit_frames,
        "investigate": investigate_frames,
        "sleep":       sleep_frames,
        "wake":        wake_frames,
        "happy":       happy_frames,
        "roar":        roar_frames,
        "jump":        jump_frames,
    }
    if fall_frames:
        animations["fall"] = fall_frames
        animations["drag"] = drag_frames
        animations["land"] = land_frames
    if climb_up_frames:
        animations["climb_up"] = climb_up_frames
        animations["climb_up_flip"] = climb_up_flip_frames
        animations["climb_down"] = climb_down_frames
        animations["climb_down_flip"] = climb_down_flip_frames
        animations["climb_perch"] = climb_perch_frames
        animations["climb_perch_flip"] = climb_perch_flip_frames

    print(f"Generating HD Spider-Man Noir sprite sheets into {OUT_DIR}...")
    for name, frames in animations.items():
        s = sheet(frames)
        path = OUT_DIR / f"{name}.png"
        s.save(path, format="PNG")
        print(f"  OK {name}.png ({len(frames)} frames, {s.width}x{s.height}px)")
    print("All HD Spider-Noir sprite sheets successfully generated!")


if __name__ == "__main__":
    generate_all()

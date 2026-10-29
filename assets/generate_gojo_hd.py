"""
HD Sprite Generator for Chibi Satoru Gojo (Limitless / Jujutsu Kaisen).
Generates 256x256 high-resolution, smooth animation sheets from the authentic
character reference sheets:
- Smooth walking cycle with hands-in-pocket strut (walk_right / walk_left)
- Idle standing with subtle breathing & cursed aura shimmer (idle / idle_flip)
- Chibi sitting with cute front & crossed-arms pouts (sit)
- Sleeping slumber with floating comic Zzz bubbles (sleep)
- Surprised alert wake-up with "!!" marks and sweat drops (wake)
- Cute pouting & smiling expressions (blink)
- Cheerful victory stride with arms up & golden sparkles (happy)
- Cursed Technique Reversal: RED & Repulsive Blast (roar)
- Cursed Technique Lapse: BLUE & Gravitational Pull (investigate)
- Leap / Skip airborne jump (jump)
- Limitless floating / falling with aura shield (fall)
- Clean landing crouch with impact puff (land)
- Dragged / picked up by cursor (drag)
- Screen edge wall crawl & infinity perch (climb_up, climb_down, climb_perch)
"""

from pathlib import Path
import math
import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw, ImageFilter

SOURCE_DIR = Path(__file__).parent / "source"
WALK_SRC = SOURCE_DIR / "gojo_walk.jpg"
POSES_SRC = SOURCE_DIR / "gojo_poses.jpg"
SKILLS_SRC = SOURCE_DIR / "gojo_skills.jpg"

OUT_DIR = Path(__file__).parent / "sprites" / "gojo"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_SIZE = 256
GROUND_Y = 244


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


def draw_glow(canvas: Image.Image, center: tuple[int, int], radius: int, color=(0, 160, 255, 140)):
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


def draw_zzz(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color=(120, 200, 255, 230)):
    # Cute comic Z
    w = size
    h = int(size * 1.2)
    draw.line([x, y, x + w, y], fill=color, width=2)
    draw.line([x + w, y, x, y + h], fill=color, width=2)
    draw.line([x, y + h, x + w, y + h], fill=color, width=2)


def draw_exclamation(draw: ImageDraw.ImageDraw, x: int, y: int, color=(255, 70, 70, 255)):
    draw.line([x, y, x, y + 16], fill=color, width=3)
    draw.ellipse([x - 2, y + 20, x + 2, y + 24], fill=color)


def extract_figure(im: Image.Image, box: tuple[int, int, int, int], bg_thresh: float = 38.0) -> Image.Image:
    crop = im.crop(box)
    arr = np.array(crop, dtype=np.float32)

    corners = np.concatenate([arr[:6, :6], arr[:6, -6:], arr[-6:, :6], arr[-6:, -6:]], axis=0)
    bg = np.median(corners, axis=(0, 1))
    dist = np.linalg.norm(arr - bg, axis=2)

    passable = dist < bg_thresh
    seed = np.zeros(passable.shape, dtype=bool)
    seed[0, :] = True
    seed[-1, :] = True
    seed[:, 0] = True
    seed[:, -1] = True
    seed &= passable
    outer_bg = ndi.binary_propagation(seed, mask=passable)

    fg = ~outer_bg
    lbl, num = ndi.label(fg)
    if num > 0:
        counts = np.bincount(lbl.ravel())[1:]
        keep_ids = np.where(counts > 300)[0] + 1
        if len(keep_ids) > 0:
            fg = np.isin(lbl, keep_ids)
        else:
            fg = (lbl == (np.argmax(counts) + 1))
    outer_bg = ~fg

    dilated_fg = ndi.binary_dilation(fg, iterations=1)
    edge_zone = dilated_fg & ~fg

    alpha = np.zeros(fg.shape, dtype=np.float32)
    alpha[fg] = 1.0
    alpha[edge_zone] = np.clip(dist[edge_zone] / 40.0, 0.0, 1.0)

    rgb = arr[:, :, :3].copy()
    for c in range(3):
        denom = np.maximum(alpha, 0.05)
        unblended = (rgb[:, :, c] - (1.0 - alpha) * bg[c]) / denom
        rgb[:, :, c] = np.clip(np.where(alpha > 0.02, unblended, rgb[:, :, c]), 0.0, 255.0)

    rgba = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def place_grounded(sprite: Image.Image, target_height: int = 205, ground_y: int = GROUND_Y, offset_x: int = 0) -> Image.Image:
    canvas = make_canvas()
    sw, sh = sprite.size
    scale = target_height / float(sh)
    nw = max(1, int(round(sw * scale)))
    nh = target_height

    resized = sprite.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (CANVAS_SIZE - nw) // 2 + offset_x
    y = ground_y - nh
    canvas.paste(resized, (x, y), resized)
    return canvas


def place_centered(sprite: Image.Image, target_height: int = 205, offset_y: int = 0, offset_x: int = 0) -> Image.Image:
    canvas = make_canvas()
    sw, sh = sprite.size
    scale = target_height / float(sh)
    nw = max(1, int(round(sw * scale)))
    nh = target_height

    resized = sprite.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (CANVAS_SIZE - nw) // 2 + offset_x
    y = (CANVAS_SIZE - nh) // 2 + offset_y
    canvas.paste(resized, (x, y), resized)
    return canvas


def generate_all():
    print("Loading Gojo reference images…")
    w_im = Image.open(WALK_SRC).convert("RGB")
    p_im = Image.open(POSES_SRC).convert("RGB")
    s_im = Image.open(SKILLS_SRC).convert("RGB")

    print("Extracting individual poses…")
    # Walk figures
    walk_start   = extract_figure(w_im, (70, 50, 260, 360))
    walk_step    = extract_figure(w_im, (300, 50, 490, 360))
    walk_stride1 = extract_figure(w_im, (540, 50, 720, 360))
    walk_stride2 = extract_figure(w_im, (770, 50, 950, 360))

    cheerful_stride = extract_figure(w_im, (110, 390, 320, 720))
    leap_skip       = extract_figure(w_im, (420, 390, 630, 720))
    strut_pocket    = extract_figure(w_im, (710, 390, 920, 720))

    # Poses & Heads
    sit_front        = extract_figure(p_im, (60, 40, 310, 400))
    sit_side         = extract_figure(p_im, (315, 40, 530, 400))
    sit_back         = extract_figure(p_im, (530, 40, 740, 400))
    sit_arms_crossed = extract_figure(p_im, (535, 450, 725, 730))

    head_laughing    = extract_figure(p_im, (50, 460, 290, 690))
    head_angry       = extract_figure(p_im, (295, 470, 515, 690))
    head_surprised   = extract_figure(p_im, (50, 750, 275, 980))
    head_sleepy      = extract_figure(p_im, (500, 750, 715, 980))

    # Skills Blue & Red
    blue_gather  = extract_figure(s_im, (60, 45, 290, 360))
    blue_lapse   = extract_figure(s_im, (360, 45, 640, 360))
    blue_pull    = extract_figure(s_im, (680, 45, 1010, 360))

    red_generate = extract_figure(s_im, (100, 400, 300, 720))
    red_reversal = extract_figure(s_im, (330, 400, 640, 720))
    red_blast    = extract_figure(s_im, (665, 400, 1000, 720))

    print("Building sprite sheets…")

    # 1. Idle (6 frames) – rhythmic breathing, slight eye sparkle
    idle_frames = []
    base_idle = place_grounded(walk_start, target_height=205)
    for i in range(6):
        c = make_canvas()
        # Rhythmic vertical breath
        breath = int(math.sin(i * math.pi / 3.0) * 2)
        bh = 205 + breath
        scaled = place_grounded(walk_start, target_height=bh)
        c.paste(scaled, (0, 0), scaled)

        # Subtle blindfold glimmer
        d = ImageDraw.Draw(c)
        if i in (1, 2):
            draw_cross_sparkle(d, 168, 106 - breath, 4, (200, 240, 255, 180))
        idle_frames.append(c)

    sheet(idle_frames).save(OUT_DIR / "idle.png")
    sheet([f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in idle_frames]).save(OUT_DIR / "idle_flip.png")

    # 2. Walk Right / Left (8 frames) – smooth authentic walk sequence
    walk_seq = [
        (walk_start, 205),
        (walk_step, 204),
        (walk_stride1, 205),
        (walk_stride2, 205),
        (strut_pocket, 206),
        (walk_stride2, 205),
        (walk_stride1, 205),
        (walk_step, 204),
    ]
    walk_frames = []
    for sp, th in walk_seq:
        walk_frames.append(place_grounded(sp, target_height=th))

    sheet(walk_frames).save(OUT_DIR / "walk_right.png")
    sheet([f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in walk_frames]).save(OUT_DIR / "walk_left.png")

    # 3. Sit (4 frames) – cute sitting with front & arms-crossed poses
    sit_frames = []
    # Frame 0 & 1: sit_front with gentle breath
    for i in range(2):
        sf = place_grounded(sit_front, target_height=180 + i, ground_y=244)
        sit_frames.append(sf)
    # Frame 2 & 3: sit_arms_crossed (cool pouting sit)
    for i in range(2):
        sc = place_grounded(sit_arms_crossed, target_height=178 + i, ground_y=244)
        sit_frames.append(sc)
    sheet(sit_frames).save(OUT_DIR / "sit.png")

    # 4. Sleep (6 frames) – snoozing Gojo with animated floating Zzz letters
    sleep_frames = []
    base_sleep = place_grounded(sit_front, target_height=180, ground_y=244)
    # Overlay head_sleepy
    hs_resized = head_sleepy.resize((150, 144), Image.Resampling.LANCZOS)
    for i in range(6):
        c = make_canvas()
        breath = int(math.sin(i * math.pi / 3.0) * 2)
        c.paste(base_sleep, (0, breath), base_sleep)
        c.paste(hs_resized, (53, 62 + breath), hs_resized)

        d = ImageDraw.Draw(c)
        # Floating Zzz
        z_y1 = 80 - (i * 5)
        z_y2 = 60 - (i * 6)
        z_y3 = 40 - (i * 7)
        draw_zzz(d, 175, z_y1, 10, (140, 210, 255, 220))
        if i >= 1:
            draw_zzz(d, 190, z_y2, 13, (120, 195, 255, 190))
        if i >= 2:
            draw_zzz(d, 205, z_y3, 16, (100, 180, 255, 160))
        sleep_frames.append(c)
    sheet(sleep_frames).save(OUT_DIR / "sleep.png")

    # 5. Wake (4 frames) – surprised / alert with "!!" and sweat drop
    wake_frames = []
    base_wake = place_grounded(sit_front, target_height=180, ground_y=244)
    hw_resized = head_surprised.resize((156, 146), Image.Resampling.LANCZOS)
    for i in range(4):
        c = make_canvas()
        c.paste(base_wake, (0, 0), base_wake)
        c.paste(hw_resized, (50, 60), hw_resized)

        d = ImageDraw.Draw(c)
        # Exclamation marks
        draw_exclamation(d, 195, 45 - i * 2, (255, 60, 60, 255))
        draw_exclamation(d, 205, 40 - i * 2, (255, 60, 60, 255))
        # Little sweat drop
        d.ellipse([185, 110, 191, 118], fill=(120, 210, 255, 230))
        wake_frames.append(c)
    sheet(wake_frames).save(OUT_DIR / "wake.png")

    # 6. Blink (4 frames) – cute expression change (smile -> pouting -> smile)
    blink_frames = []
    blink_frames.append(place_grounded(walk_start, target_height=205))
    # Overlay pouting head
    ha_resized = head_angry.resize((154, 146), Image.Resampling.LANCZOS)
    for i in range(2):
        c = place_grounded(walk_start, target_height=205)
        c.paste(ha_resized, (51, 38), ha_resized)
        blink_frames.append(c)
    blink_frames.append(place_grounded(walk_start, target_height=205))
    sheet(blink_frames).save(OUT_DIR / "blink.png")

    # 7. Happy (8 frames) – Cheerful Stride with arms raised in joy & golden sparkles!
    happy_frames = []
    base_happy = place_grounded(cheerful_stride, target_height=210)
    for i in range(8):
        c = make_canvas()
        bounce = -int(math.sin(i * math.pi / 4.0) * 8)
        c.paste(base_happy, (0, bounce), base_happy)

        d = ImageDraw.Draw(c)
        # Sparkling stars around Gojo
        angles = [0.0, 1.2, 2.5, 3.8, 5.0]
        for idx, ang in enumerate(angles):
            sparkle_ang = ang + (i * 0.4)
            dist_s = 75 + (idx * 8)
            sx = int(128 + math.cos(sparkle_ang) * dist_s)
            sy = int(120 + math.sin(sparkle_ang) * 55) + bounce
            if 10 < sx < 245 and 10 < sy < 245:
                color = (255, 220, 90, 240) if idx % 2 == 0 else (130, 230, 255, 240)
                draw_cross_sparkle(d, sx, sy, 5 + (i % 3), color)
        happy_frames.append(c)
    sheet(happy_frames).save(OUT_DIR / "happy.png")

    # 8. Roar (8 frames) – CURSED TECHNIQUE REVERSAL: RED & REPULSIVE BLAST!
    roar_frames = []
    # Frame 0-1: Generating Red (spark on fingertip)
    f0 = place_grounded(red_generate, target_height=205)
    draw_glow(f0, (82, 168), 12, (255, 60, 60, 200))
    roar_frames.append(f0)

    f1 = place_grounded(red_generate, target_height=205)
    draw_glow(f1, (82, 168), 18, (255, 40, 40, 240))
    roar_frames.append(f1)

    # Frame 2-4: Cursed Technique Reversal: Red (swirling red vortex & red lightning)
    for i in range(3):
        rf = place_grounded(red_reversal, target_height=205, offset_x=12)
        draw_glow(rf, (102, 172), 26 + i * 4, (255, 20, 50, 230))
        d = ImageDraw.Draw(rf)
        # Red lightning crackles
        for _ in range(4):
            lx = 102 + np.random.randint(-25, 25)
            ly = 172 + np.random.randint(-25, 25)
            d.line([102, 172, lx, ly], fill=(255, 200, 200, 240), width=2)
        roar_frames.append(rf)

    # Frame 5-7: Repulsive Blast (explosive blast beam & energy shockwave)
    for i in range(3):
        bf = place_grounded(red_blast, target_height=205, offset_x=-15)
        draw_glow(bf, (55, 170), 38 + i * 8, (255, 30, 60, 220))
        d = ImageDraw.Draw(bf)
        # Shockwave rings
        for rad in range(25, 65, 14):
            d.arc([55 - rad, 170 - rad, 55 + rad, 170 + rad], start=120, end=240, fill=(255, 180, 180, 220), width=3)
        roar_frames.append(bf)

    sheet(roar_frames).save(OUT_DIR / "roar.png")

    # 9. Investigate (8 frames) – CURSED TECHNIQUE LAPSE: BLUE & GRAVITATIONAL PULL!
    investigate_frames = []
    # Frame 0-1: Gathering Blue (swirling orb on fingertip)
    ib0 = place_grounded(blue_gather, target_height=205)
    draw_glow(ib0, (84, 98), 16, (0, 170, 255, 220))
    investigate_frames.append(ib0)

    ib1 = place_grounded(blue_gather, target_height=205)
    draw_glow(ib1, (84, 98), 24, (0, 210, 255, 250))
    investigate_frames.append(ib1)

    # Frame 2-4: Technique Lapse: Blue (two-handed magnetic vortex)
    for i in range(3):
        lf = place_grounded(blue_lapse, target_height=205, offset_x=10)
        draw_glow(lf, (115, 145), 32 + i * 5, (0, 150, 255, 230))
        d = ImageDraw.Draw(lf)
        # Inward spiral magnetic particles
        for p_idx in range(6):
            ang = p_idx * 1.0 + (i * 0.8)
            dist_p = 45 - (i * 6)
            px = int(115 + math.cos(ang) * dist_p)
            py = int(145 + math.sin(ang) * dist_p)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(200, 240, 255, 240))
        investigate_frames.append(lf)

    # Frame 5-7: Gravitational Pull (firing blue sphere with aura waves)
    for i in range(3):
        pf = place_grounded(blue_pull, target_height=205, offset_x=12)
        draw_glow(pf, (78, 142), 35 + i * 6, (0, 180, 255, 240))
        d = ImageDraw.Draw(pf)
        # Curved blue aura shockwaves
        for rad in range(30, 75, 15):
            d.arc([78 - rad, 142 - rad, 78 + rad, 142 + rad], start=-70, end=70, fill=(180, 235, 255, 220), width=3)
        investigate_frames.append(pf)

    sheet(investigate_frames).save(OUT_DIR / "investigate.png")

    # 10. Jump (4 frames) – Leap / Skip airborne jump
    jump_frames = []
    base_jump = place_centered(leap_skip, target_height=205, offset_y=-10)
    for i in range(4):
        c = make_canvas()
        offset_y = -15 - int(math.sin(i * math.pi / 3.0) * 20)
        jf = place_centered(leap_skip, target_height=205, offset_y=offset_y)
        c.paste(jf, (0, 0), jf)

        d = ImageDraw.Draw(c)
        # Wind lines below feet
        for wx in (100, 128, 155):
            d.line([wx, 215, wx, 235], fill=(220, 220, 230, 180), width=2)
        jump_frames.append(c)
    sheet(jump_frames).save(OUT_DIR / "jump.png")

    # 11. Fall (5 frames) – Limitless floating descent with infinity aura
    fall_frames = []
    base_fall = place_centered(leap_skip, target_height=205)
    for i in range(5):
        c = make_canvas()
        tilt = int(math.sin(i * 1.2) * 5)
        # Gentle floating infinity barrier aura
        draw_glow(c, (128, 128), 75, (160, 220, 255, 90))
        c.paste(base_fall, (tilt, 0), base_fall)

        d = ImageDraw.Draw(c)
        # Upward wind streaks
        for wy in range(40, 210, 45):
            wx = 60 + ((wy * 7) % 130)
            d.line([wx, wy, wx, wy + 20], fill=(240, 240, 255, 170), width=2)
        fall_frames.append(c)
    sheet(fall_frames).save(OUT_DIR / "fall.png")

    # 12. Land (4 frames) – landing impact crouch
    land_frames = []
    land_crouch = place_grounded(walk_start, target_height=185, ground_y=244)
    for i in range(4):
        c = make_canvas()
        c.paste(land_crouch, (0, 0), land_crouch)
        d = ImageDraw.Draw(c)
        # Dust puffs on ground
        puff_w = 25 + i * 15
        d.arc([128 - puff_w, 235, 128 + puff_w, 250], start=0, end=180, fill=(200, 200, 200, 200 - i * 40), width=2)
        land_frames.append(c)
    sheet(land_frames).save(OUT_DIR / "land.png")

    # 13. Drag (2 frames) – held by user cursor with dangling motion
    drag_frames = []
    drag_sp = place_centered(leap_skip, target_height=195, offset_y=-5)
    for i in range(2):
        c = make_canvas()
        c.paste(drag_sp, ((-1) ** i * 3, 0), drag_sp)
        d = ImageDraw.Draw(c)
        # Motion indicator
        d.arc([118, 25, 138, 45], start=0, end=360, fill=(255, 255, 255, 180), width=2)
        drag_frames.append(c)
    sheet(drag_frames).save(OUT_DIR / "drag.png")

    # 14. Climb Up & Down (4 frames each) – Wall crawling / leaping
    climb_frames = []
    for sp in (walk_step, walk_stride1, walk_stride2, strut_pocket):
        rotated = sp.rotate(-90, expand=True, resample=Image.Resampling.BICUBIC)
        climb_frames.append(place_centered(rotated, target_height=195, offset_x=-15))

    sheet(climb_frames).save(OUT_DIR / "climb_up.png")
    sheet([f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in climb_frames]).save(OUT_DIR / "climb_up_flip.png")
    sheet(climb_frames[::-1]).save(OUT_DIR / "climb_down.png")
    sheet([f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in climb_frames[::-1]]).save(OUT_DIR / "climb_down_flip.png")

    # 15. Climb Perch (4 frames) – sitting on the edge of the screen
    perch_frames = []
    base_perch = place_grounded(sit_side, target_height=190, ground_y=244, offset_x=-30)
    for i in range(4):
        c = make_canvas()
        breath = int(math.sin(i * math.pi / 2.0) * 2)
        c.paste(base_perch, (0, breath), base_perch)
        perch_frames.append(c)

    sheet(perch_frames).save(OUT_DIR / "climb_perch.png")
    sheet([f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in perch_frames]).save(OUT_DIR / "climb_perch_flip.png")

    print(f"All Chibi Satoru Gojo HD sprite sheets generated in {OUT_DIR}!")


if __name__ == "__main__":
    generate_all()

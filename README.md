# Desktop Pet: Satoru Gojo & Spider-Man Noir 🤞🕷️

A delightful desktop pet featuring **Chibi Satoru Gojo** (Limitless / Jujutsu Kaisen) and **Spider-Man Noir** living and wandering on your desktop!

---

## Features

### 🤞 Chibi Satoru Gojo
Based directly on authentic reference sheets:
- **Smooth Walking Cycle & Strut**: Complete walking cycle with stepping forward, stride, and iconic hands-in-pockets cool strut!
- **Idle Stance**: Natural standing idle with subtle breathing and blindfold cursed aura shimmer.
- **Chibi Sitting**: Cute sitting pose resting on bottom bar + pouting arms-crossed pose.
- **Sleep & Nap**: Cute snoozing face with animated floating comic "Zzz" bubbles.
- **Surprised Alert Wake-Up**: Popping "!!" marks, wide-eyed surprise, and sweat drop.
- **Pouting & Expressions**: Subtle cute cheek pouting and smile toggling.
- **Cheerful Victory Stride**: Both arms raised high with sparkling golden stars.
- **🔵 Cursed Technique Lapse: Blue**: Gathering Blue on fingertip -> Intense magnetic lapse vortex -> Gravitational Pull finger-gun with shockwaves!
- **🔴 Cursed Technique Reversal: Red**: Generating Red spark on fingertip -> Swirling singularity with red lightning -> Explosive Repulsive Blast!
- **⚡ Leap / Jump & Wall Perch**: Leaps across the screen and perches on screen edges.

### 🕷️ Spider-Man Noir
- Hard-boiled detective Rubik's cube, radio mishap, and wall-crawling.
- Web-zip leap and case notes on crate actions.

### Character Hot-Swapping
- Switch between **🤞 Satoru Gojo** and **🕷️ Spider-Man Noir** at any time!
- Switch instantly via **Right-Click -> Character** or the Settings dialog.

---

## Installation & Launch

### Quick Launch
Double-click:
- `start_gojo.bat` (Launches Chibi Satoru Gojo directly!)
- `start_spider_noir.bat` (Launches Spider-Man Noir directly!)

### Manual Launch
```bash
pip install -r requirements.txt
python main.py gojo
```

Sprites for characters are automatically generated into `assets/sprites/` on first launch.

---

## Controls

- **Left-Click + Drag**: Grab and move the pet anywhere on your screen with your mouse!
  - Dragging near the screen bottom snaps the pet onto the Windows taskbar.
  - Dragging near the top snaps it to the top edge.
  - Dropping anywhere in the middle keeps it walking at that custom height!
- **Left-Click**: Trigger character interaction (Rubik's cube / Gojo action).
- **Double-Click**: Trigger character special action.
- **Right-Click**: Open Context Menu:
  - **Placement**: Switch between `⬇️ Screen Bottom (Taskbar)` and `⬆️ Screen Top`.
  - **Techniques / Actions**: Trigger any action instantly on demand.
  - **Character**: Switch between `🤞 Satoru Gojo` and `🕷️ Spider-Man Noir` on the fly.
  - **Pause / Resume**: Keep the pet resting in place.
  - **Settings…**: Adjust size, animation speed, movement speed, dock placement, and startup options.
  - **Exit**: Close the pet.

---

## Project Structure

```
Desktop-Pet/
├── assets/
│   ├── generate_gojo_hd.py        # Gojo HD sprite generator
│   ├── generate_spider_noir_hd.py # Spider-Noir HD sprite generator
│   └── sprites/
│       ├── gojo/                  # Gojo PNG sprite sheets
│       └── spider_noir/           # Spider-Noir PNG sprite sheets
├── animation.py                   # Multi-character sprite sheet loader & frame ticker
├── movement.py                    # State machine (idle/walk/sit/sleep/jump/special)
├── settings.py                    # Settings persistence + UI dialog (character picker)
├── startup.py                     # Windows registry auto-start helper
├── lion.py                        # Desktop pet overlay window & Win32 click-through
├── main.py                        # Entry point & sprite validation
├── start_gojo.bat                 # One-click Gojo launcher
├── start_spider_noir.bat          # One-click Spider-Noir launcher
└── requirements.txt
```
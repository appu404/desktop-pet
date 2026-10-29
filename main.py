from __future__ import annotations
import sys
import os
from pathlib import Path

# Ensure the project root is on sys.path when launched as a script
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from settings import Settings
import startup


def ensure_sprites():
    sprite_dir = PROJECT_ROOT / "assets" / "sprites"
    noir_dir = sprite_dir / "spider_noir"
    gojo_dir = sprite_dir / "gojo"

    noir_dir.mkdir(parents=True, exist_ok=True)
    gojo_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(PROJECT_ROOT / "assets"))

    # Generate Satoru Gojo HD sprites if missing
    if not (gojo_dir / "idle.png").exists() or not any(gojo_dir.glob("*.png")):
        print("Generating Chibi Satoru Gojo HD sprites…")
        try:
            import generate_gojo_hd
            generate_gojo_hd.generate_all()
        except Exception as e:
            print(f"Warning: Gojo sprite generation failed – {e}")

    # Generate Spider-Man Noir sprites if missing
    if not (noir_dir / "climb_up.png").exists() or not any(noir_dir.glob("*.png")):
        print("Generating Spider-Man Noir HD sprites…")
        try:
            import generate_spider_noir_hd
            generate_spider_noir_hd.generate_all()
        except Exception:
            try:
                import generate_spider_noir
                generate_spider_noir.generate_all(noir_dir)
            except Exception as e:
                print(f"Warning: Spider-Noir sprite generation failed – {e}")


def main():
    # Ensure window is attached to user's interactive 'Default' desktop
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

    # High-DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setOrganizationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)   # keep alive via tray

    # Pixel-perfect rendering: disable font antialiasing effects
    font = QFont()
    font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
    app.setFont(font)

    ensure_sprites()

    settings = Settings()
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("gojo", "spider_noir"):
        settings.character = sys.argv[1].lower()
    elif settings.character not in ("gojo", "spider_noir"):
        settings.character = "gojo"
    startup.sync_startup(settings.start_with_windows)

    # Import here so Qt app exists before widget construction
    from lion import LionWindow
    window = LionWindow(settings)

    sys.exit(app.exec())



if __name__ == "__main__":
    main()

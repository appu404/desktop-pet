from __future__ import annotations
import ctypes
import ctypes.wintypes
import time

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QPixmap, QImage, QAction
from PySide6.QtWidgets import QWidget, QApplication, QMenu

from animation import AnimationController
from movement import MovementController, STATE_TO_ANIM, LionState
from settings import Settings, SettingsDialog
import startup

# ── Win32 constants ───────────────────────────────────────────────────────────
GWL_EXSTYLE      = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WM_NCHITTEST     = 0x0084
HTTRANSPARENT    = -1
HTCLIENT         = 1

_user32 = ctypes.windll.user32

# Set argtypes so ctypes handles HWND/BOOL correctly
_user32.GetWindowLongW.argtypes  = [ctypes.wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongW.restype   = ctypes.c_long
_user32.SetWindowLongW.argtypes  = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_long]
_user32.SetWindowLongW.restype   = ctypes.c_long
_user32.GetWindowRect.argtypes   = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
_user32.GetWindowRect.restype    = ctypes.wintypes.BOOL


def _hwnd(widget: QWidget) -> int:
    return int(widget.winId())


def _apply_extended_styles(hwnd: int):
    style = _user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    _user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)


class LionWindow(QWidget):
    FRAME_MS = 16   # ~60 fps

    def __init__(self, settings: Settings):
        super().__init__(None)
        self._settings = settings
        self._paused = False
        self._last_frame_time = time.monotonic()
        self._pet_size = settings.pet_size

        char = getattr(settings, "character", "gojo")
        self._anim = AnimationController(fps=settings.animation_fps, character=char)
        self._move = MovementController(
            walk_speed=settings.walk_speed,
            inactivity_sleep=15.0,
            pet_size=self._pet_size,
            dock_position="bottom",
        )

        self._is_dragging = False
        self._drag_start_pos: QPoint | None = None
        self._window_start_pos: QPoint | None = None

        self._current_pixmap: QPixmap | None = None

        self._build_window()
        self._update_title()
        self._setup_timer()


    # ── Window setup ──────────────────────────────────────────────────────────

    def _build_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setWindowTitle("DesktopPet")

        # Set geometry BEFORE show() so Qt does NOT apply its default centering
        self.setGeometry(self._move.x, self._move.y, self._pet_size, self._pet_size)
        self.show()

        # Apply additional Win32 styles after the HWND exists
        _apply_extended_styles(_hwnd(self))

    # ── Timer / game loop ─────────────────────────────────────────────────────

    def _setup_timer(self):
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self.FRAME_MS)

    def _tick(self):
        now = time.monotonic()
        delta = now - self._last_frame_time
        self._last_frame_time = now

        if self._paused or self._is_dragging:
            return

        self._move.update(delta)

        anim_name = STATE_TO_ANIM.get(self._move.state, "idle")
        self._anim.set_state(anim_name)

        # Qt tracks position correctly when we use move()
        new_x = self._move.x
        new_y = self._move.y
        if self.x() != new_x or self.y() != new_y:
            self.move(new_x, new_y)

        self.update()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        raw: QPixmap = self._anim.tick()
        size = self._pet_size
        char = getattr(self._settings, "character", "gojo")
        is_hd = (char in ("spider_noir", "gojo") or raw.width() > 64)
        transform_mode = (
            Qt.TransformationMode.SmoothTransformation
            if is_hd
            else Qt.TransformationMode.FastTransformation
        )

        if raw.width() != size or raw.height() != size:
            raw = raw.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                transform_mode,
            )
        self._current_pixmap = raw

        painter = QPainter(self)
        if is_hd:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        else:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawPixmap(0, 0, raw)
        painter.end()


    # ── Click-through via WM_NCHITTEST ────────────────────────────────────────

    def nativeEvent(self, event_type: bytes, message) -> tuple:
        if event_type == b"windows_generic_MSG":
            msg = ctypes.cast(
                int(message),
                ctypes.POINTER(ctypes.wintypes.MSG)
            ).contents
            if msg.message == WM_NCHITTEST:
                lp = msg.lParam
                sx = ctypes.c_int16(lp & 0xFFFF).value
                sy = ctypes.c_int16((lp >> 16) & 0xFFFF).value
                rect = ctypes.wintypes.RECT()
                _user32.GetWindowRect(_hwnd(self), ctypes.byref(rect))
                lx = sx - rect.left
                ly = sy - rect.top
                if self._is_opaque(lx, ly):
                    return True, HTCLIENT
                return True, HTTRANSPARENT
        return super().nativeEvent(event_type, message)

    def _is_opaque(self, lx: int, ly: int) -> bool:
        if self._current_pixmap is None:
            return False
        size = self._pet_size
        if lx < 0 or ly < 0 or lx >= size or ly >= size:
            return False
        img = self._current_pixmap.toImage().convertToFormat(
            QImage.Format.Format_ARGB32
        )
        alpha = (img.pixel(lx, ly) >> 24) & 0xFF
        return alpha > 30

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            self._window_start_pos = self.pos()
            self._is_dragging = False
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            if not self._is_dragging and delta.manhattanLength() > 4:
                self._is_dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self._move.start_drag()
                self._anim.set_state("drag")

            if self._is_dragging:
                rect = self._move._get_available_geometry()
                new_x = self._window_start_pos.x() + delta.x()
                new_y = self._window_start_pos.y() + delta.y()
                # Clamp within screen bounds
                new_x = max(rect.left(), min(new_x, rect.right() - self._pet_size + 1))
                new_y = max(rect.top(), min(new_y, rect.bottom() - self._pet_size + 1))
                self.move(new_x, new_y)
                self._move.set_pos(new_x, new_y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.unsetCursor()
            if getattr(self, "_is_dragging", False):
                self._is_dragging = False
                cur_y = self.y()
                bottom_y = self._move._get_bottom_y()

                # Pet is only placeable on bottom.
                # If released anywhere above the bottom floor, trigger falling down effect!
                if cur_y < bottom_y - 4:
                    self._move.start_falling()
                    self._anim.set_state("fall")
                else:
                    self._move.set_pos(self.x(), bottom_y)
                    self.move(self.x(), bottom_y)
                    self._anim.set_state("idle")
                    self._move.resume()
            else:
                if self._move.state not in (LionState.FALLING, LionState.LANDING):
                    self._move.trigger_happy()
                    self._anim.set_state("happy")

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._move.trigger_roar()
            self._anim.set_state("roar")

    def _update_title(self):
        char = getattr(self._settings, "character", "gojo")
        if char == "gojo":
            self.setWindowTitle("Chibi Satoru Gojo")
        elif char == "spider_noir":
            self.setWindowTitle("Pixel Spider-Noir")
        else:
            self.setWindowTitle("Desktop Pet")

    # ── Context menu ──────────────────────────────────────────────────────────

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu()
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Character selection submenu
        char_menu = menu.addMenu("Character")
        current_char = getattr(self._settings, "character", "gojo")

        gojo_action = QAction("🤞 Satoru Gojo", self)
        gojo_action.setCheckable(True)
        gojo_action.setChecked(current_char == "gojo")
        gojo_action.triggered.connect(lambda: self._set_character("gojo"))
        char_menu.addAction(gojo_action)

        spider_action = QAction("🕷️ Spider-Man Noir", self)
        spider_action.setCheckable(True)
        spider_action.setChecked(current_char == "spider_noir")
        spider_action.triggered.connect(lambda: self._set_character("spider_noir"))
        char_menu.addAction(spider_action)

        # Actions submenu
        if current_char == "gojo":
            actions_menu = menu.addMenu("🤞 Gojo Techniques")

            blue_act = QAction("🔵 Cursed Technique Lapse: Blue", self)
            blue_act.triggered.connect(lambda: (self._move.trigger_investigate(), self._anim.set_state("investigate")))
            actions_menu.addAction(blue_act)

            red_act = QAction("🔴 Reversal: Red & Repulsive Blast", self)
            red_act.triggered.connect(lambda: (self._move.trigger_roar(), self._anim.set_state("roar")))
            actions_menu.addAction(red_act)

            happy_act = QAction("✨ Cheerful Victory Stride", self)
            happy_act.triggered.connect(lambda: (self._move.trigger_happy(), self._anim.set_state("happy")))
            actions_menu.addAction(happy_act)

            sit_act = QAction("🪑 Chibi Sit", self)
            sit_act.triggered.connect(lambda: (self._move.trigger_sit(), self._anim.set_state("sit")))
            actions_menu.addAction(sit_act)

            jump_act = QAction("⚡ Leap / Skip Jump", self)
            jump_act.triggered.connect(lambda: (self._move.trigger_jump(), self._anim.set_state("jump")))
            actions_menu.addAction(jump_act)

            climb_l_act = QAction("🧗 Wall Perch Left", self)
            climb_l_act.triggered.connect(lambda: (self._move.start_climb("left"), self._anim.set_state("climb_up")))
            actions_menu.addAction(climb_l_act)

            climb_r_act = QAction("🧗 Wall Perch Right", self)
            climb_r_act.triggered.connect(lambda: (self._move.start_climb("right"), self._anim.set_state("climb_up_flip")))
            actions_menu.addAction(climb_r_act)

            sleep_act = QAction("💤 Nap / Snooze (Zzz)", self)
            sleep_act.triggered.connect(lambda: (self._move.trigger_sleep(), self._anim.set_state("sleep")))
            actions_menu.addAction(sleep_act)
        else:
            actions_menu = menu.addMenu("🕷️ Noir Actions")

            rubik_act = QAction("🎲 Solve Rubik's Cube", self)
            rubik_act.triggered.connect(lambda: (self._move.trigger_happy(), self._anim.set_state("happy")))
            actions_menu.addAction(rubik_act)

            radio_act = QAction("📻 Radio & Web Mishap", self)
            radio_act.triggered.connect(lambda: (self._move.trigger_roar(), self._anim.set_state("roar")))
            actions_menu.addAction(radio_act)

            notes_act = QAction("📝 Case Notes (Sit on Crate)", self)
            notes_act.triggered.connect(lambda: (self._move.trigger_investigate(), self._anim.set_state("investigate")))
            actions_menu.addAction(notes_act)

            sit_act = QAction("🪑 Take a Seat", self)
            sit_act.triggered.connect(lambda: (self._move.trigger_sit(), self._anim.set_state("sit")))
            actions_menu.addAction(sit_act)

            jump_act = QAction("🕸️ Web-Zip Leap", self)
            jump_act.triggered.connect(lambda: (self._move.trigger_jump(), self._anim.set_state("jump")))
            actions_menu.addAction(jump_act)

            climb_l_act = QAction("🧗 Crawl Left Screen Edge", self)
            climb_l_act.triggered.connect(lambda: (self._move.start_climb("left"), self._anim.set_state("climb_up")))
            actions_menu.addAction(climb_l_act)

            climb_r_act = QAction("🧗 Crawl Right Screen Edge", self)
            climb_r_act.triggered.connect(lambda: (self._move.start_climb("right"), self._anim.set_state("climb_up_flip")))
            actions_menu.addAction(climb_r_act)

            sleep_act = QAction("💤 Take a Nap", self)
            sleep_act.triggered.connect(lambda: (self._move.trigger_sleep(), self._anim.set_state("sleep")))
            actions_menu.addAction(sleep_act)

        menu.addSeparator()

        pause_action = QAction("Pause", self)
        pause_action.setCheckable(True)
        pause_action.setChecked(self._paused)
        pause_action.toggled.connect(self._toggle_pause)
        menu.addAction(pause_action)

        menu.addSeparator()

        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)

        menu.exec(pos)

    def _set_character(self, character_name: str):
        self._settings.character = character_name
        self._settings.save()
        self._anim.set_character(character_name)
        self._update_title()
        self.update()

    def _toggle_pause(self, checked: bool):
        self._paused = checked
        if checked:
            self._move.pause()
        else:
            self._move.resume()

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, parent=None)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()

    def _apply_settings(self, s: Settings):
        char = getattr(s, "character", "spider_noir")
        self._anim.set_character(char)
        self._update_title()
        self._anim.set_fps(s.animation_fps)
        self._move.walk_speed = s.walk_speed
        self._pet_size = s.pet_size
        self._move.pet_size = s.pet_size
        self.resize(s.pet_size, s.pet_size)

        self._move.set_dock_position("bottom")
        self.move(self._move.x, self._move.y)

        startup.sync_startup(s.start_with_windows)
        self.update()


    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._timer.stop()
        event.accept()

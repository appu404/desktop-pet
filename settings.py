from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QCheckBox, QPushButton, QGroupBox, QFormLayout, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, Signal


CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "PixelLion"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS: dict[str, Any] = {
    "character":        "gojo",
    "animation_fps":    12,
    "walk_speed":       60,
    "pet_size":         108,
    "screen_dock":      "bottom",
    "custom_y":         0,
    "sounds_enabled":   False,
    "start_with_windows": True,
    "always_on_top":    True,
}




class Settings:
    """Load/save settings; attribute access for individual values."""

    def __init__(self):
        self._data: dict[str, Any] = dict(DEFAULTS)
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in loaded.items():
                    if k in DEFAULTS:
                        self._data[k] = v
                if self._data.get("character") not in ("gojo", "spider_noir"):
                    self._data["character"] = "gojo"
                    self.save()
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._data:
            return self._data[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any):
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif name in DEFAULTS:
            self._data[name] = value
            self.save()
        else:
            super().__setattr__(name, value)

    def get(self, key: str, default=None):
        return self._data.get(key, default)


class SettingsDialog(QDialog):
    settings_changed = Signal(object)   # emits updated Settings instance

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._s = settings
        self.setWindowTitle("Desktop Pet – Settings")
        self.setMinimumWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Character group ──────────────────────────────────────────────────
        char_group = QGroupBox("Character")
        char_form = QFormLayout(char_group)

        self._char_combo = QComboBox()
        self._char_combo.addItem("🤞 Satoru Gojo (Limitless)", "gojo")
        self._char_combo.addItem("🕷️ Spider-Man Noir", "spider_noir")
        current_char = getattr(self._s, "character", "gojo")
        idx = self._char_combo.findData(current_char)
        if idx >= 0:
            self._char_combo.setCurrentIndex(idx)
        char_form.addRow("Pet Character:", self._char_combo)
        layout.addWidget(char_group)

        # ── Animation group ──────────────────────────────────────────────────
        anim_group = QGroupBox("Animation")
        anim_form = QFormLayout(anim_group)

        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(4, 30)
        self._fps_spin.setValue(self._s.animation_fps)
        self._fps_spin.setSuffix(" fps")
        anim_form.addRow("Animation Speed:", self._fps_spin)

        layout.addWidget(anim_group)


        # ── Movement group ───────────────────────────────────────────────────
        move_group = QGroupBox("Movement")
        move_form = QFormLayout(move_group)

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(20, 200)
        self._speed_slider.setValue(self._s.walk_speed)
        self._speed_label = QLabel(f"{self._s.walk_speed} px/s")
        self._speed_slider.valueChanged.connect(
            lambda v: self._speed_label.setText(f"{v} px/s")
        )
        spd_row = QHBoxLayout()
        spd_row.addWidget(self._speed_slider)
        spd_row.addWidget(self._speed_label)
        move_form.addRow("Walking Speed:", spd_row)

        self._size_spin = QSpinBox()
        self._size_spin.setRange(48, 256)
        self._size_spin.setSingleStep(8)
        self._size_spin.setValue(self._s.pet_size)
        self._size_spin.setSuffix(" px")
        move_form.addRow("Pet Size:", self._size_spin)

        dock_label = QLabel("⬇️ Screen Bottom (Taskbar)")
        dock_label.setStyleSheet("color: #888;")
        move_form.addRow("Placement:", dock_label)

        layout.addWidget(move_group)

        # ── Sound group ──────────────────────────────────────────────────────
        sound_group = QGroupBox("Sound")
        sound_layout = QVBoxLayout(sound_group)
        self._sound_cb = QCheckBox("Enable sounds")
        self._sound_cb.setChecked(self._s.sounds_enabled)
        sound_layout.addWidget(self._sound_cb)
        layout.addWidget(sound_group)

        # ── System group ─────────────────────────────────────────────────────
        sys_group = QGroupBox("System")
        sys_layout = QVBoxLayout(sys_group)
        self._startup_cb = QCheckBox("Start with Windows")
        self._startup_cb.setChecked(self._s.start_with_windows)
        self._ontop_cb = QCheckBox("Always on top")
        self._ontop_cb.setChecked(self._s.always_on_top)
        sys_layout.addWidget(self._startup_cb)
        sys_layout.addWidget(self._ontop_cb)
        layout.addWidget(sys_group)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._apply_and_close)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _apply_and_close(self):
        self._s.character = self._char_combo.currentData()
        self._s.animation_fps = self._fps_spin.value()
        self._s.walk_speed = self._speed_slider.value()
        self._s.pet_size = self._size_spin.value()
        self._s.screen_dock = "bottom"
        self._s.sounds_enabled = self._sound_cb.isChecked()
        self._s.start_with_windows = self._startup_cb.isChecked()
        self._s.always_on_top = self._ontop_cb.isChecked()
        self._s.save()
        self.settings_changed.emit(self._s)
        self.accept()

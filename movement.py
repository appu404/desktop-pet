from __future__ import annotations
import random
import time
from enum import Enum, auto
from dataclasses import dataclass, field

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect


class LionState(Enum):
    IDLE        = auto()
    WALK_LEFT   = auto()
    WALK_RIGHT  = auto()
    SIT         = auto()
    SLEEP       = auto()
    WAKING      = auto()
    BLINKING    = auto()
    HAPPY       = auto()
    ROARING     = auto()
    JUMPING     = auto()
    INVESTIGATE = auto()
    FALLING     = auto()
    LANDING     = auto()
    DRAGGED     = auto()
    CLIMB_UP_LEFT    = auto()
    CLIMB_DOWN_LEFT  = auto()
    WALL_PERCH_LEFT  = auto()
    CLIMB_UP_RIGHT   = auto()
    CLIMB_DOWN_RIGHT = auto()
    WALL_PERCH_RIGHT = auto()

PetState = LionState


# How long (seconds) the pet stays in each state before reconsidering
STATE_DURATION = {
    LionState.IDLE:        (1.0,  4.0),
    LionState.WALK_LEFT:   (2.0,  6.0),
    LionState.WALK_RIGHT:  (2.0,  6.0),
    LionState.SIT:         (3.0,  8.0),
    LionState.SLEEP:       (8.0, 20.0),
    LionState.WAKING:      (1.5,  1.5),
    LionState.BLINKING:    (0.4,  0.4),
    LionState.HAPPY:       (2.0,  2.5),
    LionState.ROARING:     (2.0,  2.5),
    LionState.JUMPING:     (0.8,  0.8),
    LionState.INVESTIGATE: (3.5,  8.0),
    LionState.FALLING:     (9999.0, 9999.0),
    LionState.LANDING:     (0.5,  0.5),
    LionState.DRAGGED:     (9999.0, 9999.0),
    LionState.CLIMB_UP_LEFT:    (9999.0, 9999.0),
    LionState.CLIMB_DOWN_LEFT:  (9999.0, 9999.0),
    LionState.WALL_PERCH_LEFT:  (1.5, 3.0),
    LionState.CLIMB_UP_RIGHT:   (9999.0, 9999.0),
    LionState.CLIMB_DOWN_RIGHT: (9999.0, 9999.0),
    LionState.WALL_PERCH_RIGHT: (1.5, 3.0),
}

# Probability weights for autonomous transitions from IDLE
IDLE_TRANSITIONS = {
    LionState.WALK_LEFT:   25,
    LionState.WALK_RIGHT:  25,
    LionState.SIT:         15,
    LionState.INVESTIGATE: 15,
    LionState.BLINKING:    10,
    LionState.JUMPING:      5,
    LionState.IDLE:         5,
}

PIXELS_PER_SECOND = 60   # walking speed (pixels / sec)
CLIMB_SPEED = 70         # wall crawling upward speed (pixels / sec)
CLIMB_DOWN_SPEED = 120   # wall crawling downward speed (pixels / sec)
PET_SIZE = 48
INACTIVITY_SLEEP = 15.0  # seconds of no user-triggered action before pet sleeps


@dataclass
class MovementController:
    walk_speed: float = PIXELS_PER_SECOND
    climb_speed: float = CLIMB_SPEED
    climb_down_speed: float = CLIMB_DOWN_SPEED
    inactivity_sleep: float = INACTIVITY_SLEEP
    pet_size: int = 96
    dock_position: str = "bottom"   # Bottom only
    custom_y: int = 0

    _state: LionState = field(default=LionState.IDLE, init=False)
    _x: float = field(default=0.0, init=False)
    _y: float = field(default=0.0, init=False)
    _vy: float = field(default=0.0, init=False)
    _climb_target_y: float = field(default=0.0, init=False)
    _state_until: float = field(default=0.0, init=False)
    _last_user_action: float = field(default_factory=time.monotonic, init=False)
    _screen_width: int = field(default=1920, init=False)

    def __post_init__(self):
        rect = self._get_available_geometry()
        self._screen_width = rect.width()
        min_x = rect.left()
        max_x = max(min_x, rect.right() - self.pet_size + 1)
        self._x = float(random.randint(min_x, max_x))
        # Strictly placeable on bottom
        self.dock_position = "bottom"
        self._y = float(self._get_bottom_y())
        self._schedule_next(LionState.IDLE)


    # ── public API ────────────────────────────────────────────────────────────

    @property
    def x(self) -> int:
        return int(self._x)

    @x.setter
    def x(self, val: int | float):
        self._x = float(val)

    @property
    def y(self) -> int:
        return int(self._y)

    @y.setter
    def y(self, val: int | float):
        self._y = float(val)

    def set_pos(self, x: int | float, y: int | float):
        self._x = float(x)
        self._y = float(y)
        self._last_user_action = time.monotonic()

    def set_dock_position(self, dock: str = "bottom", custom_y: int | None = None):
        # Pet is strictly placeable on bottom
        self.dock_position = "bottom"
        self._y = float(self._get_bottom_y())
        self._last_user_action = time.monotonic()

    @property
    def state(self) -> LionState:
        return self._state

    @property
    def is_climbing(self) -> bool:
        return self._state in (
            LionState.CLIMB_UP_LEFT, LionState.CLIMB_DOWN_LEFT, LionState.WALL_PERCH_LEFT,
            LionState.CLIMB_UP_RIGHT, LionState.CLIMB_DOWN_RIGHT, LionState.WALL_PERCH_RIGHT
        )

    def start_drag(self):
        self._last_user_action = time.monotonic()
        self._vy = 0.0
        self._transition(LionState.DRAGGED)

    def start_falling(self, initial_vy: float = 0.0):
        self._last_user_action = time.monotonic()
        self._vy = initial_vy
        self._transition(LionState.FALLING)

    def start_climb(self, side: str = "left"):
        self._last_user_action = time.monotonic()
        self._vy = 0.0
        rect = self._get_available_geometry()
        top_y = rect.top()
        bottom_y = self._get_bottom_y()
        # Random climb height between 45% and 85% up the screen
        climb_span = bottom_y - top_y
        climb_dist = random.uniform(climb_span * 0.45, climb_span * 0.85)
        self._climb_target_y = float(max(top_y + 30, bottom_y - climb_dist))

        if side == "left":
            self._x = float(rect.left())
            self._transition(LionState.CLIMB_UP_LEFT)
        else:
            self._x = float(max(rect.left(), rect.right() - self.pet_size + 1))
            self._transition(LionState.CLIMB_UP_RIGHT)

    def trigger_happy(self):
        self._last_user_action = time.monotonic()
        self._transition(LionState.HAPPY)

    def trigger_roar(self):
        self._last_user_action = time.monotonic()
        self._transition(LionState.ROARING)

    def trigger_investigate(self):
        self._last_user_action = time.monotonic()
        self._transition(LionState.INVESTIGATE)

    def trigger_sit(self):
        self._last_user_action = time.monotonic()
        self._transition(LionState.SIT)

    def trigger_sleep(self):
        self._last_user_action = time.monotonic()
        self._transition(LionState.SLEEP)

    def trigger_jump(self):
        self._last_user_action = time.monotonic()
        self._transition(LionState.JUMPING)

    def pause(self):
        self._transition(LionState.IDLE)
        # extend stay so autonomous ticks don't immediately move
        self._state_until = time.monotonic() + 9999.0

    def resume(self):
        self._state_until = time.monotonic()

    def update(self, delta: float):
        now = time.monotonic()

        # check inactivity → sleep (only when idle at bottom, not while falling/climbing/dragged)
        active_states = (
            LionState.SLEEP, LionState.WAKING, LionState.FALLING, LionState.LANDING, LionState.DRAGGED,
            LionState.CLIMB_UP_LEFT, LionState.CLIMB_DOWN_LEFT, LionState.WALL_PERCH_LEFT,
            LionState.CLIMB_UP_RIGHT, LionState.CLIMB_DOWN_RIGHT, LionState.WALL_PERCH_RIGHT
        )
        if self._state not in active_states and (now - self._last_user_action > self.inactivity_sleep):
            if self._state != LionState.SLEEP:
                self._transition(LionState.SLEEP)

        # state-machine tick for autonomous transitions
        non_advancing = (
            LionState.FALLING, LionState.DRAGGED,
            LionState.CLIMB_UP_LEFT, LionState.CLIMB_DOWN_LEFT,
            LionState.CLIMB_UP_RIGHT, LionState.CLIMB_DOWN_RIGHT
        )
        if self._state not in non_advancing and now >= self._state_until:
            self._advance_state()

        rect = self._get_available_geometry()
        min_x = rect.left()
        max_x = max(min_x, rect.right() - self.pet_size + 1)
        bottom_y = float(self._get_bottom_y())

        # position update based on state
        if self._state == LionState.WALK_LEFT:
            self._x -= self.walk_speed * delta
        elif self._state == LionState.WALK_RIGHT:
            self._x += self.walk_speed * delta
        elif self._state == LionState.FALLING:
            # Gravity acceleration downwards
            GRAVITY = 2400.0   # px / sec^2
            self._vy = min(self._vy + GRAVITY * delta, 2200.0)
            self._y += self._vy * delta
            if self._y >= bottom_y:
                self._y = bottom_y
                self._vy = 0.0
                self._transition(LionState.LANDING)

        # ── Climbing up/down screen edges ──
        elif self._state == LionState.CLIMB_UP_LEFT:
            self._x = float(min_x)
            self._y -= self.climb_speed * delta
            if self._y <= self._climb_target_y:
                self._y = self._climb_target_y
                # Smoothly transition directly into downward crawl (no sitting on air)
                self._transition(LionState.CLIMB_DOWN_LEFT)

        elif self._state == LionState.CLIMB_UP_RIGHT:
            self._x = float(max_x)
            self._y -= self.climb_speed * delta
            if self._y <= self._climb_target_y:
                self._y = self._climb_target_y
                # Smoothly transition directly into downward crawl (no sitting on air)
                self._transition(LionState.CLIMB_DOWN_RIGHT)

        elif self._state == LionState.WALL_PERCH_LEFT:
            self._x = float(min_x)
            self._y = self._climb_target_y
            self._transition(LionState.CLIMB_DOWN_LEFT)

        elif self._state == LionState.WALL_PERCH_RIGHT:
            self._x = float(max_x)
            self._y = self._climb_target_y
            self._transition(LionState.CLIMB_DOWN_RIGHT)

        elif self._state == LionState.CLIMB_DOWN_LEFT:
            self._x = float(min_x)
            self._y += self.climb_down_speed * delta
            if self._y >= bottom_y:
                self._y = bottom_y
                # Stepped off left wall back onto floor -> walk right across screen!
                self._transition(LionState.WALK_RIGHT)

        elif self._state == LionState.CLIMB_DOWN_RIGHT:
            self._x = float(max_x)
            self._y += self.climb_down_speed * delta
            if self._y >= bottom_y:
                self._y = bottom_y
                # Stepped off right wall back onto floor -> walk left across screen!
                self._transition(LionState.WALK_LEFT)

        # clamp horizontal coordinates to screen bounds
        self._x = max(float(min_x), min(self._x, float(max_x)))

        # keep Y anchored strictly to bottom when on the floor
        airborne_or_climbing = (
            LionState.FALLING, LionState.DRAGGED,
            LionState.CLIMB_UP_LEFT, LionState.CLIMB_DOWN_LEFT, LionState.WALL_PERCH_LEFT,
            LionState.CLIMB_UP_RIGHT, LionState.CLIMB_DOWN_RIGHT, LionState.WALL_PERCH_RIGHT
        )
        if self._state not in airborne_or_climbing:
            self._y = bottom_y

        # ── Wall triggers when reaching sides of screen ──
        if self._x <= min_x and self._state == LionState.WALK_LEFT:
            self._x = float(min_x)
            # Reached left screen edge: crawl up the left wall!
            self.start_climb(side="left")
        elif self._x >= max_x and self._state == LionState.WALK_RIGHT:
            self._x = float(max_x)
            # Reached right screen edge: crawl up the right wall!
            self.start_climb(side="right")


    # ── state machine ─────────────────────────────────────────────────────────

    def _advance_state(self):
        s = self._state
        if s == LionState.WALL_PERCH_LEFT:
            # Perch finished -> crawl down left wall
            self._transition(LionState.CLIMB_DOWN_LEFT)
            self._last_user_action = time.monotonic()
        elif s == LionState.WALL_PERCH_RIGHT:
            # Perch finished -> crawl down right wall
            self._transition(LionState.CLIMB_DOWN_RIGHT)
            self._last_user_action = time.monotonic()
        elif s == LionState.LANDING:
            self._transition(LionState.IDLE)
            self._last_user_action = time.monotonic()
        elif s == LionState.SLEEP:
            # wake up
            self._transition(LionState.WAKING)
            self._last_user_action = time.monotonic()
        elif s == LionState.WAKING:
            self._transition(LionState.IDLE)
        elif s in (LionState.HAPPY, LionState.ROARING, LionState.JUMPING,
                   LionState.BLINKING, LionState.INVESTIGATE):
            self._transition(LionState.IDLE)
        else:
            # weighted random autonomous choice
            choices = list(IDLE_TRANSITIONS.keys())
            weights = list(IDLE_TRANSITIONS.values())
            # avoid same direction twice if already walking
            if s in (LionState.WALK_LEFT, LionState.WALK_RIGHT):
                # prefer stopping or turning
                next_s = random.choices(
                    [LionState.IDLE, LionState.SIT, LionState.INVESTIGATE,
                     LionState.WALK_LEFT, LionState.WALK_RIGHT],
                    weights=[25, 15, 15, 25, 20]
                )[0]
            else:
                next_s = random.choices(choices, weights=weights)[0]
            self._transition(next_s)

    def _transition(self, new_state: LionState):
        self._state = new_state
        self._schedule_next(new_state)

    def _schedule_next(self, state: LionState):
        lo, hi = STATE_DURATION.get(state, (2.0, 4.0))
        self._state_until = time.monotonic() + random.uniform(lo, hi)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _get_available_geometry() -> QRect:
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                return screen.availableGeometry()
        return QRect(0, 0, 1920, 1040)

    def _get_bottom_y(self) -> int:
        rect = self._get_available_geometry()
        return max(rect.top(), rect.bottom() - self.pet_size + 1)

    def _get_top_y(self) -> int:
        rect = self._get_available_geometry()
        return rect.top()


# Map LionState → animation name string
STATE_TO_ANIM = {
    LionState.IDLE:              "idle",
    LionState.WALK_LEFT:         "walk_left",
    LionState.WALK_RIGHT:        "walk_right",
    LionState.SIT:               "sit",
    LionState.SLEEP:             "sleep",
    LionState.WAKING:            "wake",
    LionState.BLINKING:          "blink",
    LionState.HAPPY:             "happy",
    LionState.ROARING:           "roar",
    LionState.JUMPING:           "jump",
    LionState.INVESTIGATE:       "investigate",
    LionState.FALLING:           "fall",
    LionState.LANDING:           "land",
    LionState.DRAGGED:           "drag",
    LionState.CLIMB_UP_LEFT:     "climb_up",
    LionState.CLIMB_DOWN_LEFT:   "climb_up",
    LionState.WALL_PERCH_LEFT:   "climb_perch",
    LionState.CLIMB_UP_RIGHT:    "climb_up_flip",
    LionState.CLIMB_DOWN_RIGHT:  "climb_up_flip",
    LionState.WALL_PERCH_RIGHT:  "climb_perch_flip",
}

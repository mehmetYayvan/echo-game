"""Powerup module - special items with temporary effects."""

import pygame
import random
import math
from enum import Enum


class PowerupType(Enum):
    """Types of powerups."""
    GHOST_EATER = "ghost_eater"
    TIME_FREEZE = "time_freeze"
    SHRINK = "shrink"


# Powerup configurations
POWERUP_CONFIG = {
    PowerupType.GHOST_EATER: {
        "color": (255, 50, 50),       # Red
        "glow_color": (255, 50, 50, 80),
        "icon": "skull",              # Will draw a skull shape
        "duration": 5.0,
        "spawn_weight": 1,            # Rarest
        "label": "GHOST EATER",
    },
    PowerupType.TIME_FREEZE: {
        "color": (80, 180, 255),      # Ice blue
        "glow_color": (80, 180, 255, 80),
        "icon": "snowflake",          # Will draw a snowflake shape
        "duration": 5.0,
        "spawn_weight": 3,            # Common
        "label": "TIME FREEZE",
    },
    PowerupType.SHRINK: {
        "color": (180, 80, 255),      # Purple
        "glow_color": (180, 80, 255, 80),
        "icon": "diamond",            # Will draw a diamond shape
        "duration": 6.0,
        "spawn_weight": 3,            # Common
        "label": "SHRINK",
    },
}


class Powerup:
    """A powerup that spawns on the field and grants temporary effects."""

    RADIUS = 12
    MARGIN = 50

    def __init__(self, screen_width: int, screen_height: int):
        """Initialize powerup.

        Args:
            screen_width: Width of the game area.
            screen_height: Height of the game area.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0.0
        self.y = 0.0
        self.active = False
        self.powerup_type: PowerupType = PowerupType.TIME_FREEZE
        self.pulse_time = 0.0
        self.spawn_timer = 0.0
        self.spawn_interval = 8.0  # seconds between powerup spawns

    def update(self, dt: float) -> None:
        """Update powerup state.

        Args:
            dt: Delta time in seconds.
        """
        if self.active:
            self.pulse_time += dt
        else:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self._spawn()

    def _spawn(self) -> None:
        """Spawn a new powerup with weighted random type."""
        self.spawn_timer = 0.0
        self.active = True
        self.pulse_time = 0.0

        # Weighted random type selection (ghost eater is rarer)
        types = []
        for ptype, config in POWERUP_CONFIG.items():
            types.extend([ptype] * config["spawn_weight"])
        self.powerup_type = random.choice(types)

        # Random position
        self.x = random.uniform(self.MARGIN, self.screen_width - self.MARGIN)
        self.y = random.uniform(self.MARGIN, self.screen_height - self.MARGIN)

    def collect(self) -> PowerupType | None:
        """Collect the powerup.

        Returns:
            The powerup type if active, None otherwise.
        """
        if not self.active:
            return None
        self.active = False
        self.spawn_timer = 0.0
        return self.powerup_type

    def collides_with(self, px: float, py: float, pradius: float) -> bool:
        """Check collision with a circle.

        Args:
            px: Circle x position.
            py: Circle y position.
            pradius: Circle radius.

        Returns:
            True if collision detected.
        """
        if not self.active:
            return False
        dx = self.x - px
        dy = self.y - py
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (self.RADIUS + pradius)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the powerup with distinct icon per type.

        Args:
            screen: Pygame surface to draw on.
        """
        if not self.active:
            return

        config = POWERUP_CONFIG[self.powerup_type]
        color = config["color"]
        glow_color = config["glow_color"]

        # Pulsing glow
        pulse = math.sin(self.pulse_time * 5) * 0.4 + 0.8
        glow_radius = int((self.RADIUS + 16) * pulse)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (int(self.x) - glow_radius, int(self.y) - glow_radius))

        # Outer ring
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.RADIUS + 2, 2)

        # Inner fill (darker)
        dark_color = (color[0] // 3, color[1] // 3, color[2] // 3)
        pygame.draw.circle(screen, dark_color, (int(self.x), int(self.y)), self.RADIUS)

        # Draw icon based on type
        cx, cy = int(self.x), int(self.y)
        if config["icon"] == "skull":
            self._draw_skull(screen, cx, cy, color)
        elif config["icon"] == "snowflake":
            self._draw_snowflake(screen, cx, cy, color)
        elif config["icon"] == "diamond":
            self._draw_diamond(screen, cx, cy, color)

    def _draw_skull(self, screen: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        """Draw skull icon (ghost eater)."""
        # Simple skull: circle head + two eyes + teeth
        pygame.draw.circle(screen, color, (cx, cy - 1), 6, 1)
        pygame.draw.circle(screen, color, (cx - 2, cy - 2), 1)
        pygame.draw.circle(screen, color, (cx + 2, cy - 2), 1)
        pygame.draw.line(screen, color, (cx - 3, cy + 3), (cx + 3, cy + 3), 1)
        pygame.draw.line(screen, color, (cx - 1, cy + 3), (cx - 1, cy + 5), 1)
        pygame.draw.line(screen, color, (cx + 1, cy + 3), (cx + 1, cy + 5), 1)

    def _draw_snowflake(self, screen: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        """Draw snowflake icon (time freeze)."""
        # Six lines radiating from center
        length = 7
        for angle_deg in range(0, 360, 60):
            angle = math.radians(angle_deg)
            ex = cx + int(length * math.cos(angle))
            ey = cy + int(length * math.sin(angle))
            pygame.draw.line(screen, color, (cx, cy), (ex, ey), 1)
        # Center dot
        pygame.draw.circle(screen, color, (cx, cy), 2)

    def _draw_diamond(self, screen: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        """Draw diamond icon (shrink)."""
        # Small diamond shape with arrow pointing inward
        size = 6
        points = [
            (cx, cy - size),      # top
            (cx + size, cy),      # right
            (cx, cy + size),      # bottom
            (cx - size, cy),      # left
        ]
        pygame.draw.polygon(screen, color, points, 1)
        # Inner smaller diamond
        s2 = 3
        inner = [
            (cx, cy - s2),
            (cx + s2, cy),
            (cx, cy + s2),
            (cx - s2, cy),
        ]
        pygame.draw.polygon(screen, color, inner)


class ActiveEffect:
    """Tracks an active powerup effect on the player."""

    def __init__(self, powerup_type: PowerupType):
        """Initialize active effect.

        Args:
            powerup_type: Type of powerup effect.
        """
        self.powerup_type = powerup_type
        config = POWERUP_CONFIG[powerup_type]
        self.duration = config["duration"]
        self.remaining = config["duration"]
        self.label = config["label"]
        self.color = config["color"]

    def update(self, dt: float) -> bool:
        """Update effect timer.

        Args:
            dt: Delta time in seconds.

        Returns:
            True if effect is still active.
        """
        self.remaining -= dt
        return self.remaining > 0

    @property
    def progress(self) -> float:
        """Get remaining progress (1.0 = full, 0.0 = expired)."""
        return max(0.0, self.remaining / self.duration)

    def draw_indicator(self, screen: pygame.Surface, x: int, y: int) -> None:
        """Draw effect indicator bar.

        Args:
            screen: Pygame surface to draw on.
            x: X position of indicator.
            y: Y position of indicator.
        """
        bar_width = 120
        bar_height = 16

        # Background bar
        bg_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, (40, 40, 50), bg_rect)

        # Progress bar
        fill_width = int(bar_width * self.progress)
        if fill_width > 0:
            # Flash when about to expire
            color = self.color
            if self.remaining < 1.5:
                if int(self.remaining * 6) % 2 == 0:
                    color = (255, 255, 255)
            fill_rect = pygame.Rect(x, y, fill_width, bar_height)
            pygame.draw.rect(screen, color, fill_rect)

        # Border
        pygame.draw.rect(screen, self.color, bg_rect, 1)

        # Label text
        font = pygame.font.Font(None, 20)
        label = font.render(self.label, True, (255, 255, 255))
        screen.blit(label, (x + 4, y + 1))

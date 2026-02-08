"""Player module - movement and path recording."""

import pygame


class Player:
    """The player character that records its movement history."""

    RADIUS = 12
    SPEED = 4
    COLOR = (0, 200, 255)  # Cyan
    GLOW_COLOR = (0, 100, 180, 80)  # Semi-transparent glow
    TRAIL_LENGTH = 20

    def __init__(self, x: float, y: float):
        """Initialize player at given position.

        Args:
            x: Starting x position.
            y: Starting y position.
        """
        self.x = x
        self.y = y
        self.path_history: list[tuple[float, float]] = []
        self.trail: list[tuple[float, float]] = []

    def move(self, dx: float, dy: float, screen_width: int, screen_height: int) -> None:
        """Move the player and record position.

        Args:
            dx: Horizontal direction (-1, 0, or 1).
            dy: Vertical direction (-1, 0, or 1).
            screen_width: Width of the game area.
            screen_height: Height of the game area.
        """
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.x += dx * self.SPEED
        self.y += dy * self.SPEED

        # Keep player within bounds
        self.x = max(self.RADIUS, min(screen_width - self.RADIUS, self.x))
        self.y = max(self.RADIUS, min(screen_height - self.RADIUS, self.y))

        # Record position
        pos = (self.x, self.y)
        self.path_history.append(pos)

        # Update trail
        self.trail.append(pos)
        if len(self.trail) > self.TRAIL_LENGTH:
            self.trail.pop(0)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the player with trail effect.

        Args:
            screen: Pygame surface to draw on.
        """
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i + 1) / len(self.trail)) if self.trail else 255
            radius = max(2, int(self.RADIUS * (i + 1) / len(self.trail)))
            trail_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.COLOR, alpha // 3), (radius, radius), radius)
            screen.blit(trail_surface, (int(tx) - radius, int(ty) - radius))

        # Draw glow
        glow_radius = self.RADIUS + 8
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, self.GLOW_COLOR, (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (int(self.x) - glow_radius, int(self.y) - glow_radius))

        # Draw player circle
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.RADIUS)

    def reset(self, x: float, y: float) -> None:
        """Reset player to starting position.

        Args:
            x: New x position.
            y: New y position.
        """
        self.x = x
        self.y = y
        self.path_history.clear()
        self.trail.clear()

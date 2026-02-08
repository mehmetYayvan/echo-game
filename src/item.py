"""Collectible item module."""

import pygame
import random
import math


class Item:
    """A collectible item that spawns at random positions."""

    RADIUS = 8
    COLOR = (255, 220, 50)  # Gold
    GLOW_COLOR = (255, 220, 50, 60)
    MARGIN = 40  # Minimum distance from edges

    def __init__(self, screen_width: int, screen_height: int):
        """Initialize item at a random position.

        Args:
            screen_width: Width of the game area.
            screen_height: Height of the game area.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0.0
        self.y = 0.0
        self.pulse_time = 0.0
        self.respawn()

    def respawn(self) -> None:
        """Move item to a new random position."""
        self.x = random.uniform(self.MARGIN, self.screen_width - self.MARGIN)
        self.y = random.uniform(self.MARGIN, self.screen_height - self.MARGIN)
        self.pulse_time = 0.0

    def collides_with(self, px: float, py: float, pradius: float) -> bool:
        """Check if a circle collides with this item.

        Args:
            px: Circle x position.
            py: Circle y position.
            pradius: Circle radius.

        Returns:
            True if collision detected.
        """
        dx = self.x - px
        dy = self.y - py
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (self.RADIUS + pradius)

    def update(self, dt: float) -> None:
        """Update item animation.

        Args:
            dt: Delta time in seconds.
        """
        self.pulse_time += dt

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the item with pulsing glow effect.

        Args:
            screen: Pygame surface to draw on.
        """
        # Pulsing glow
        pulse = math.sin(self.pulse_time * 4) * 0.3 + 0.7
        glow_radius = int((self.RADIUS + 12) * pulse)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, self.GLOW_COLOR, (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (int(self.x) - glow_radius, int(self.y) - glow_radius))

        # Draw item circle
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.RADIUS)

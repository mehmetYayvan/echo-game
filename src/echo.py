"""Echo module - ghost that replays recorded player path."""

import pygame


# Echo color palette - each new echo gets a different color
ECHO_COLORS = [
    (255, 80, 80),    # Red
    (255, 160, 50),   # Orange
    (255, 255, 80),   # Yellow
    (80, 255, 80),    # Green
    (180, 80, 255),   # Purple
    (255, 80, 200),   # Pink
    (80, 255, 200),   # Teal
    (200, 200, 255),  # Light blue
]


class Echo:
    """A ghost that replays the player's recorded path."""

    RADIUS = 12
    TRAIL_LENGTH = 15

    def __init__(self, path: list[tuple[float, float]], color_index: int):
        """Initialize echo with a recorded path.

        Args:
            path: List of (x, y) positions to replay.
            color_index: Index into ECHO_COLORS for this echo's color.
        """
        self.path = path.copy()
        self.frame_index = 0
        self.color = ECHO_COLORS[color_index % len(ECHO_COLORS)]
        self.trail: list[tuple[float, float]] = []
        self.finished = False

    @property
    def x(self) -> float:
        """Current x position."""
        if self.frame_index < len(self.path):
            return self.path[self.frame_index][0]
        return self.path[-1][0] if self.path else 0

    @property
    def y(self) -> float:
        """Current y position."""
        if self.frame_index < len(self.path):
            return self.path[self.frame_index][1]
        return self.path[-1][1] if self.path else 0

    def update(self) -> None:
        """Advance one frame along the recorded path."""
        if self.frame_index < len(self.path):
            pos = self.path[self.frame_index]
            self.trail.append(pos)
            if len(self.trail) > self.TRAIL_LENGTH:
                self.trail.pop(0)
            self.frame_index += 1
        else:
            self.finished = True

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the echo ghost with trail.

        Args:
            screen: Pygame surface to draw on.
        """
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(150 * (i + 1) / len(self.trail)) if self.trail else 150
            radius = max(2, int(self.RADIUS * (i + 1) / len(self.trail)))
            trail_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.color, alpha // 4), (radius, radius), radius)
            screen.blit(trail_surface, (int(tx) - radius, int(ty) - radius))

        # Draw glow
        glow_radius = self.RADIUS + 6
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 40), (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (int(self.x) - glow_radius, int(self.y) - glow_radius))

        # Draw echo circle (semi-transparent)
        echo_surface = pygame.Surface((self.RADIUS * 2, self.RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(echo_surface, (*self.color, 160), (self.RADIUS, self.RADIUS), self.RADIUS)
        screen.blit(echo_surface, (int(self.x) - self.RADIUS, int(self.y) - self.RADIUS))

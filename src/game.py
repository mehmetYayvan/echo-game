"""Game module - main game loop, collision, state management."""

import pygame
import math
from enum import Enum

from src.player import Player
from src.echo import Echo
from src.item import Item
from src.powerup import Powerup, PowerupType, ActiveEffect


class GameState(Enum):
    """Game states."""
    PLAYING = "playing"
    GAME_OVER = "game_over"


# Screen settings
WIDTH = 800
HEIGHT = 600
FPS = 60
BG_COLOR = (15, 15, 25)

# Game settings
ECHO_INTERVAL = 5  # seconds between echo spawns
COLLISION_GRACE = 1.0  # seconds of grace period after echo spawn

# Player sizes
NORMAL_RADIUS = 12
SHRINK_RADIUS = 6


class Game:
    """Main game class managing all game logic."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the game.

        Args:
            screen: Pygame display surface.
        """
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 72)
        self.high_score = 0
        self.reset()

    def reset(self) -> None:
        """Reset game to initial state."""
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.echoes: list[Echo] = []
        self.item = Item(WIDTH, HEIGHT)
        self.powerup = Powerup(WIDTH, HEIGHT)
        self.active_effects: list[ActiveEffect] = []
        self.score = 0
        self.echo_timer = 0.0
        self.echo_count = 0
        self.game_time = 0.0
        self.state = GameState.PLAYING
        self.ghosts_eaten = 0

    def _has_effect(self, powerup_type: PowerupType) -> bool:
        """Check if a powerup effect is currently active."""
        return any(e.powerup_type == powerup_type for e in self.active_effects)

    def run(self) -> bool:
        """Run the game loop.

        Returns:
            False when the game should quit.
        """
        while True:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                        self.reset()

            if self.state == GameState.PLAYING:
                self._update(dt)
            self._draw()

        return True

    def _update(self, dt: float) -> None:
        """Update game logic.

        Args:
            dt: Delta time in seconds.
        """
        self.game_time += dt

        # Update active effects
        self.active_effects = [e for e in self.active_effects if e.update(dt)]

        # Apply shrink effect to player
        if self._has_effect(PowerupType.SHRINK):
            self.player.RADIUS = SHRINK_RADIUS
        else:
            self.player.RADIUS = NORMAL_RADIUS

        # Handle movement input
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        self.player.move(dx, dy, WIDTH, HEIGHT)

        # Spawn echoes on interval (frozen echoes don't affect timer)
        self.echo_timer += dt
        if self.echo_timer >= ECHO_INTERVAL:
            self.echo_timer = 0.0
            new_echo = Echo(self.player.path_history, self.echo_count)
            self.echoes.append(new_echo)
            self.echo_count += 1

        # Update echoes (skip if time freeze active)
        if not self._has_effect(PowerupType.TIME_FREEZE):
            for echo in self.echoes:
                echo.update()

        # Update items
        self.item.update(dt)
        self.powerup.update(dt)

        # Check item collection
        if self.item.collides_with(self.player.x, self.player.y, self.player.RADIUS):
            self.score += 1
            self.item.respawn()

        # Check powerup collection
        if self.powerup.collides_with(self.player.x, self.player.y, self.player.RADIUS):
            ptype = self.powerup.collect()
            if ptype:
                self.active_effects.append(ActiveEffect(ptype))

        # Check collision with echoes
        if self.game_time > COLLISION_GRACE:
            is_ghost_eater = self._has_effect(PowerupType.GHOST_EATER)
            for echo in self.echoes[:]:  # Copy list since we may modify
                if echo.frame_index > FPS * COLLISION_GRACE:
                    dist = math.sqrt(
                        (self.player.x - echo.x) ** 2 +
                        (self.player.y - echo.y) ** 2
                    )
                    if dist < (self.player.RADIUS + echo.RADIUS - 4):
                        if is_ghost_eater:
                            self.echoes.remove(echo)
                            self.ghosts_eaten += 1
                            self.score += 3  # Bonus points for eating
                        else:
                            self._game_over()
                            return

    def _game_over(self) -> None:
        """Handle game over."""
        self.state = GameState.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score

    def _draw(self) -> None:
        """Draw everything to screen."""
        self.screen.fill(BG_COLOR)

        # Tint screen during effects
        if self._has_effect(PowerupType.TIME_FREEZE):
            tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            tint.fill((40, 80, 140, 20))
            self.screen.blit(tint, (0, 0))
        elif self._has_effect(PowerupType.GHOST_EATER):
            tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            tint.fill((140, 30, 30, 15))
            self.screen.blit(tint, (0, 0))

        # Draw item
        self.item.draw(self.screen)

        # Draw powerup
        self.powerup.draw(self.screen)

        # Draw echoes
        for echo in self.echoes:
            echo.draw(self.screen)

        # Draw player (with visual effect if powered up)
        self._draw_player()

        # Draw UI
        self._draw_ui()

        # Draw active effect indicators
        self._draw_effects()

        # Draw game over overlay
        if self.state == GameState.GAME_OVER:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_player(self) -> None:
        """Draw player with powerup visual modifications."""
        if self._has_effect(PowerupType.GHOST_EATER):
            # Override player color to red during ghost eater
            original_color = self.player.COLOR
            self.player.COLOR = (255, 80, 80)
            self.player.draw(self.screen)
            self.player.COLOR = original_color
        elif self._has_effect(PowerupType.SHRINK):
            # Purple tint during shrink
            original_color = self.player.COLOR
            self.player.COLOR = (180, 80, 255)
            self.player.draw(self.screen)
            self.player.COLOR = original_color
        else:
            self.player.draw(self.screen)

    def _draw_ui(self) -> None:
        """Draw score and info overlay."""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 15))

        # High score
        if self.high_score > 0:
            hs_text = self.small_font.render(f"Best: {self.high_score}", True, (100, 100, 120))
            self.screen.blit(hs_text, (20, 50))

        # Echo countdown
        time_to_next = ECHO_INTERVAL - self.echo_timer
        countdown_text = self.small_font.render(f"Next echo: {time_to_next:.1f}s", True, (100, 100, 120))
        self.screen.blit(countdown_text, (WIDTH - 180, 15))

        # Echo count
        echo_text = self.small_font.render(f"Echoes: {len(self.echoes)}", True, (100, 100, 120))
        self.screen.blit(echo_text, (WIDTH - 180, 45))

    def _draw_effects(self) -> None:
        """Draw active powerup effect indicators."""
        y = HEIGHT - 30
        for effect in self.active_effects:
            effect.draw_indicator(self.screen, 20, y)
            y -= 24

    def _draw_game_over(self) -> None:
        """Draw game over overlay."""
        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Game over text
        go_text = self.big_font.render("GAME OVER", True, (255, 80, 80))
        go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        self.screen.blit(go_text, go_rect)

        # Final score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        self.screen.blit(score_text, score_rect)

        # Ghosts eaten
        if self.ghosts_eaten > 0:
            eaten_text = self.small_font.render(f"Ghosts eaten: {self.ghosts_eaten}", True, (255, 80, 80))
            eaten_rect = eaten_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 15))
            self.screen.blit(eaten_text, eaten_rect)

        # High score
        if self.high_score > 0:
            hs_text = self.font.render(f"Best: {self.high_score}", True, (255, 220, 50))
            hs_rect = hs_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            self.screen.blit(hs_text, hs_rect)

        # Restart instruction
        restart_text = self.small_font.render("Press R to restart | ESC to quit", True, (150, 150, 150))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3))
        self.screen.blit(restart_text, restart_rect)

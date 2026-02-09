"""Game module - main game loop, collision, state management."""
import asyncio
import pygame
import math
from enum import Enum

try:
    from player import Player
    from echo import Echo
    from item import Item
    from powerup import Powerup, PowerupType, ActiveEffect
    from sound import SoundManager
except ImportError:
    from src.player import Player
    from src.echo import Echo
    from src.item import Item
    from src.powerup import Powerup, PowerupType, ActiveEffect
    from src.sound import SoundManager


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

# Konami code: ↑↑↓↓←→←→BA
KONAMI_CODE = [
    pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT,
    pygame.K_b, pygame.K_a,
]


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
        self.sound = SoundManager()
        self.disco_mode = False
        self.konami_buffer: list[int] = []
        self.disco_flash_timer = 0.0
        self.reset()
        self.sound.play_music()

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

    async def run(self) -> bool:
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
                    self._check_konami(event.key)

            if self.state == GameState.PLAYING:
                self._update(dt)
            self._draw()
            await asyncio.sleep(0)

        return True

    def _update(self, dt: float) -> None:
        """Update game logic.

        Args:
            dt: Delta time in seconds.
        """
        self.game_time += dt

        # Update disco flash timer
        if self.disco_flash_timer > 0:
            self.disco_flash_timer -= dt

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
            self.sound.play("echo_spawn")

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
            self.sound.play("collect_item")

        # Check powerup collection
        if self.powerup.collides_with(self.player.x, self.player.y, self.player.RADIUS):
            ptype = self.powerup.collect()
            if ptype:
                self.active_effects.append(ActiveEffect(ptype))
                self.sound.play(f"pickup_{ptype.value}")

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
                            self.sound.play("ghost_eaten")
                        else:
                            self._game_over()
                            return

    def _check_konami(self, key: int) -> None:
        """Track key presses and activate disco mode on Konami code."""
        self.konami_buffer.append(key)
        if len(self.konami_buffer) > len(KONAMI_CODE):
            self.konami_buffer.pop(0)
        if self.konami_buffer == KONAMI_CODE and not self.disco_mode:
            self.disco_mode = True
            self.disco_flash_timer = 2.0
            self.sound.play("konami_jingle")
            self.sound.play_disco_music()

    @staticmethod
    def _disco_color(offset: float, speed: float = 3.0) -> tuple[int, int, int]:
        """Generate a rainbow color cycling over time."""
        r = int((math.sin(offset * speed) * 0.5 + 0.5) * 255)
        g = int((math.sin(offset * speed + 2.094) * 0.5 + 0.5) * 255)
        b = int((math.sin(offset * speed + 4.189) * 0.5 + 0.5) * 255)
        return (r, g, b)

    def _game_over(self) -> None:
        """Handle game over."""
        self.state = GameState.GAME_OVER
        self.sound.play("game_over")
        if self.score > self.high_score:
            self.high_score = self.score

    def _draw(self) -> None:
        """Draw everything to screen."""
        if self.disco_mode:
            # Pulsing dark background with color tint
            dc = self._disco_color(self.game_time, 1.5)
            bg = (dc[0] // 15 + 10, dc[1] // 15 + 10, dc[2] // 15 + 10)
            self.screen.fill(bg)
        else:
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

        # Draw echoes (rainbow colors in disco mode)
        for i, echo in enumerate(self.echoes):
            if self.disco_mode:
                echo.color = self._disco_color(self.game_time + i * 0.5)
            echo.draw(self.screen)

        # Draw player (with visual effect if powered up)
        self._draw_player()

        # Draw UI
        self._draw_ui()

        # Draw active effect indicators
        self._draw_effects()

        # Draw disco mode activation flash
        if self.disco_flash_timer > 0:
            alpha = int(255 * min(1.0, self.disco_flash_timer))
            disco_text = self.big_font.render("DISCO MODE", True,
                                              self._disco_color(self.game_time, 8.0))
            disco_rect = disco_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
            self.screen.blit(disco_text, disco_rect)

        # Draw game over overlay
        if self.state == GameState.GAME_OVER:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_player(self) -> None:
        """Draw player with powerup visual modifications."""
        original_color = self.player.COLOR
        if self.disco_mode:
            self.player.COLOR = self._disco_color(self.game_time + 3.0)
        elif self._has_effect(PowerupType.GHOST_EATER):
            self.player.COLOR = (255, 80, 80)
        elif self._has_effect(PowerupType.SHRINK):
            self.player.COLOR = (180, 80, 255)
        self.player.draw(self.screen)
        self.player.COLOR = original_color

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

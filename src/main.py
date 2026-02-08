"""Main entry point for Echo game."""

import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.player import Player
from src.echo import Echo
from src.item import Item

# Screen settings
WIDTH = 800
HEIGHT = 600
FPS = 60
BG_COLOR = (15, 15, 25)

# Echo settings
ECHO_INTERVAL = 5  # seconds between echo spawns


def main():
    """Run the game."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Echo")
    clock = pygame.time.Clock()

    player = Player(WIDTH // 2, HEIGHT // 2)
    echoes: list[Echo] = []
    echo_timer = 0.0
    echo_count = 0
    item = Item(WIDTH, HEIGHT)
    score = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

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

        player.move(dx, dy, WIDTH, HEIGHT)

        # Spawn echoes on interval
        echo_timer += dt
        if echo_timer >= ECHO_INTERVAL:
            echo_timer = 0.0
            new_echo = Echo(player.path_history, echo_count)
            echoes.append(new_echo)
            echo_count += 1

        # Update echoes
        for echo in echoes:
            echo.update()

        # Update item
        item.update(dt)

        # Check item collection
        if item.collides_with(player.x, player.y, player.RADIUS):
            score += 1
            item.respawn()

        # Draw
        screen.fill(BG_COLOR)
        item.draw(screen)
        for echo in echoes:
            echo.draw(screen)
        player.draw(screen)

        # Draw UI
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 15))

        info_font = pygame.font.Font(None, 28)
        time_to_next = ECHO_INTERVAL - echo_timer
        countdown_text = info_font.render(f"Next echo: {time_to_next:.1f}s", True, (100, 100, 120))
        screen.blit(countdown_text, (WIDTH - 180, 15))

        echo_text = info_font.render(f"Echoes: {len(echoes)}", True, (100, 100, 120))
        screen.blit(echo_text, (WIDTH - 180, 45))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

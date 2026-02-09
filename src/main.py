"""Main entry point for Echo game."""
import asyncio
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from game import Game, WIDTH, HEIGHT
except ImportError:
    from src.game import Game, WIDTH, HEIGHT


async def main():
    """Run the game."""
    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Echo")

    game = Game(screen)
    await game.run()

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())

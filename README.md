# Echo

An original arcade game where your past movements become your enemy.

## Concept

Move around collecting items to score points. Every 5 seconds, a ghost spawns that replays your exact movements from the start. The longer you survive, the more ghosts chase your old paths. One touch with an echo and it's game over.

Your history is your enemy.

## Installation

```bash
cd echo-game
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

## Controls

- **WASD / Arrow Keys** - Move
- **R** - Restart after game over
- **ESC** - Quit

## How It Works

1. Move around the arena collecting glowing items
2. After 5 seconds, your first echo spawns - it replays your exact path
3. Every 5 seconds, another echo joins
4. Avoid all echoes while collecting items
5. The arena gets increasingly chaotic as your past selves multiply
6. Grab powerups to turn the tide

## Powerups

Powerups spawn periodically as glowing orbs with distinct icons:

| Powerup | Color | Icon | Effect |
|---------|-------|------|--------|
| **Ghost Eater** | Red | Skull | Become invincible - touching echoes destroys them (+3 pts each) |
| **Time Freeze** | Ice Blue | Snowflake | Freezes all echoes in place |
| **Shrink** | Purple | Diamond | Player becomes tiny and harder to hit |

- Ghost Eater is rarer than the others
- Each powerup lasts ~5 seconds
- Active effects show as a timer bar at the bottom of the screen
- Player changes color while a powerup is active

## Tech Stack

- Python 3.10+
- Pygame (rendering, input, game loop)

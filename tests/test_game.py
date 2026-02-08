"""Tests for Echo game logic."""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.player import Player
from src.echo import Echo, ECHO_COLORS
from src.item import Item
from src.powerup import Powerup, PowerupType, ActiveEffect, POWERUP_CONFIG


class TestPlayer:
    """Tests for Player class."""

    def test_initial_position(self):
        """Player should start at given position."""
        p = Player(100, 200)
        assert p.x == 100
        assert p.y == 200

    def test_move_right(self):
        """Player should move right."""
        p = Player(100, 100)
        p.move(1, 0, 800, 600)
        assert p.x > 100

    def test_move_left(self):
        """Player should move left."""
        p = Player(100, 100)
        p.move(-1, 0, 800, 600)
        assert p.x < 100

    def test_move_up(self):
        """Player should move up (y decreases)."""
        p = Player(100, 100)
        p.move(0, -1, 800, 600)
        assert p.y < 100

    def test_move_down(self):
        """Player should move down (y increases)."""
        p = Player(100, 100)
        p.move(0, 1, 800, 600)
        assert p.y > 100

    def test_path_recording(self):
        """Player should record movement path."""
        p = Player(100, 100)
        p.move(1, 0, 800, 600)
        p.move(1, 0, 800, 600)
        assert len(p.path_history) == 2

    def test_boundary_left(self):
        """Player should not go past left boundary."""
        p = Player(5, 100)
        p.move(-1, 0, 800, 600)
        assert p.x >= p.RADIUS

    def test_boundary_right(self):
        """Player should not go past right boundary."""
        p = Player(795, 100)
        p.move(1, 0, 800, 600)
        assert p.x <= 800 - p.RADIUS

    def test_boundary_top(self):
        """Player should not go past top boundary."""
        p = Player(100, 5)
        p.move(0, -1, 800, 600)
        assert p.y >= p.RADIUS

    def test_boundary_bottom(self):
        """Player should not go past bottom boundary."""
        p = Player(100, 595)
        p.move(0, 1, 800, 600)
        assert p.y <= 600 - p.RADIUS

    def test_reset(self):
        """Reset should clear path and move to new position."""
        p = Player(100, 100)
        p.move(1, 0, 800, 600)
        p.move(1, 0, 800, 600)
        p.reset(400, 300)
        assert p.x == 400
        assert p.y == 300
        assert len(p.path_history) == 0

    def test_diagonal_normalization(self):
        """Diagonal movement should be normalized."""
        p1 = Player(100, 100)
        p1.move(1, 0, 800, 600)
        horizontal_dist = p1.x - 100

        p2 = Player(100, 100)
        p2.move(1, 1, 800, 600)
        diagonal_x_dist = p2.x - 100

        # Diagonal x distance should be less than horizontal
        assert diagonal_x_dist < horizontal_dist


class TestEcho:
    """Tests for Echo class."""

    def test_initial_position(self):
        """Echo should start at first path position."""
        path = [(50.0, 50.0), (60.0, 50.0), (70.0, 50.0)]
        e = Echo(path, 0)
        assert e.x == 50.0
        assert e.y == 50.0

    def test_path_replay(self):
        """Echo should follow recorded path."""
        path = [(50.0, 50.0), (60.0, 50.0), (70.0, 50.0)]
        e = Echo(path, 0)
        e.update()  # Move to frame 1
        assert e.x == 60.0
        e.update()  # Move to frame 2
        assert e.x == 70.0

    def test_finished_flag(self):
        """Echo should set finished when path ends."""
        path = [(50.0, 50.0), (60.0, 50.0)]
        e = Echo(path, 0)
        e.update()  # frame 0 -> 1
        e.update()  # frame 1 -> 2
        e.update()  # frame 2 >= len(path), finished
        assert e.finished is True

    def test_color_cycling(self):
        """Each echo should get a different color."""
        e1 = Echo([(0, 0)], 0)
        e2 = Echo([(0, 0)], 1)
        assert e1.color != e2.color

    def test_path_is_copied(self):
        """Echo should copy the path, not reference it."""
        path = [(50.0, 50.0)]
        e = Echo(path, 0)
        path.append((100.0, 100.0))
        assert len(e.path) == 1


class TestItem:
    """Tests for Item class."""

    def test_spawn_within_bounds(self):
        """Item should spawn within screen bounds."""
        item = Item(800, 600)
        assert Item.MARGIN <= item.x <= 800 - Item.MARGIN
        assert Item.MARGIN <= item.y <= 600 - Item.MARGIN

    def test_respawn_changes_position(self):
        """Respawn should move item (statistically)."""
        item = Item(800, 600)
        positions = set()
        for _ in range(10):
            item.respawn()
            positions.add((round(item.x), round(item.y)))
        # Very unlikely all 10 respawns land on same spot
        assert len(positions) > 1

    def test_collision_detection(self):
        """Item should detect collision with nearby circle."""
        item = Item(800, 600)
        item.x = 100
        item.y = 100
        # Circle right on top of item
        assert item.collides_with(100, 100, 12) is True

    def test_no_collision_when_far(self):
        """Item should not detect collision when far away."""
        item = Item(800, 600)
        item.x = 100
        item.y = 100
        assert item.collides_with(400, 400, 12) is False


class TestPowerup:
    """Tests for Powerup class."""

    def test_starts_inactive(self):
        """Powerup should start inactive."""
        p = Powerup(800, 600)
        assert p.active is False

    def test_spawns_after_interval(self):
        """Powerup should spawn after timer expires."""
        p = Powerup(800, 600)
        for _ in range(100):
            p.update(0.1)  # 10 seconds total
        assert p.active is True

    def test_collect_returns_type(self):
        """Collecting active powerup should return its type."""
        p = Powerup(800, 600)
        # Force spawn
        for _ in range(100):
            p.update(0.1)
        ptype = p.collect()
        assert ptype in [PowerupType.GHOST_EATER, PowerupType.TIME_FREEZE, PowerupType.SHRINK]

    def test_collect_deactivates(self):
        """Collecting powerup should deactivate it."""
        p = Powerup(800, 600)
        for _ in range(100):
            p.update(0.1)
        p.collect()
        assert p.active is False

    def test_collect_inactive_returns_none(self):
        """Collecting inactive powerup should return None."""
        p = Powerup(800, 600)
        assert p.collect() is None

    def test_no_collision_when_inactive(self):
        """Inactive powerup should not collide."""
        p = Powerup(800, 600)
        assert p.collides_with(p.x, p.y, 12) is False

    def test_ghost_eater_is_rarer(self):
        """Ghost eater should have lower spawn weight."""
        ge_weight = POWERUP_CONFIG[PowerupType.GHOST_EATER]["spawn_weight"]
        tf_weight = POWERUP_CONFIG[PowerupType.TIME_FREEZE]["spawn_weight"]
        sh_weight = POWERUP_CONFIG[PowerupType.SHRINK]["spawn_weight"]
        assert ge_weight < tf_weight
        assert ge_weight < sh_weight


class TestActiveEffect:
    """Tests for ActiveEffect class."""

    def test_initial_progress(self):
        """Effect should start at full progress."""
        e = ActiveEffect(PowerupType.TIME_FREEZE)
        assert e.progress == 1.0

    def test_effect_expires(self):
        """Effect should expire after duration."""
        e = ActiveEffect(PowerupType.TIME_FREEZE)
        duration = POWERUP_CONFIG[PowerupType.TIME_FREEZE]["duration"]
        result = e.update(duration + 1)
        assert result is False

    def test_effect_active_during_duration(self):
        """Effect should be active within duration."""
        e = ActiveEffect(PowerupType.TIME_FREEZE)
        result = e.update(1.0)
        assert result is True
        assert 0 < e.progress < 1.0

    def test_each_type_has_different_color(self):
        """Each powerup type should have a distinct color."""
        colors = set()
        for ptype in PowerupType:
            e = ActiveEffect(ptype)
            colors.add(e.color)
        assert len(colors) == 3

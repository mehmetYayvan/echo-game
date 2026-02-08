"""Sound module - procedural audio generation for all game sounds."""

import math
import struct
import pygame

SAMPLE_RATE = 44100


def _tone(frequency: float, duration: float, volume: float = 0.3,
          wave: str = "sine", fade_out: float = 0.0) -> bytes:
    """Generate raw PCM samples for a tone.

    Args:
        frequency: Tone frequency in Hz.
        duration: Duration in seconds.
        volume: Volume from 0.0 to 1.0.
        wave: Wave type - "sine", "square", or "triangle".
        fade_out: Duration of fade-out at end, in seconds.

    Returns:
        Raw PCM bytes (16-bit signed mono).
    """
    n_samples = int(SAMPLE_RATE * duration)
    fade_samples = int(SAMPLE_RATE * fade_out) if fade_out > 0 else 0
    buf = bytearray(n_samples * 2)

    for i in range(n_samples):
        t = i / SAMPLE_RATE

        if wave == "sine":
            val = math.sin(2 * math.pi * frequency * t)
        elif wave == "square":
            val = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
        elif wave == "triangle":
            phase = (frequency * t) % 1.0
            val = 4.0 * abs(phase - 0.5) - 1.0
        else:
            val = math.sin(2 * math.pi * frequency * t)

        # Apply fade out
        if fade_samples > 0 and i >= n_samples - fade_samples:
            fade = (n_samples - i) / fade_samples
            val *= fade

        sample = int(val * volume * 32767)
        sample = max(-32768, min(32767, sample))
        struct.pack_into('<h', buf, i * 2, sample)

    return bytes(buf)


def _silence(duration: float) -> bytes:
    """Generate silence."""
    return b'\x00\x00' * int(SAMPLE_RATE * duration)


def _mix(*buffers: bytes) -> bytes:
    """Mix multiple sample buffers together (average to prevent clipping)."""
    if not buffers:
        return b''
    max_len = max(len(b) for b in buffers)
    result = bytearray(max_len)

    for i in range(0, max_len, 2):
        total = 0
        count = 0
        for buf in buffers:
            if i + 1 < len(buf):
                total += struct.unpack_from('<h', buf, i)[0]
                count += 1
        if count > 0:
            mixed = max(-32768, min(32767, total // count))
            struct.pack_into('<h', result, i, mixed)

    return bytes(result)


def _concat(*buffers: bytes) -> bytes:
    """Concatenate sample buffers."""
    return b''.join(buffers)


class SoundManager:
    """Generates and manages all game sounds procedurally."""

    def __init__(self):
        """Initialize and generate all sounds."""
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                self.enabled = False
                return
            self._generate_sfx()
            self._generate_music()
        except Exception:
            self.enabled = False

    def _generate_sfx(self) -> None:
        """Generate all sound effects."""
        # Item collected - quick ascending bleep
        self.collect_item = pygame.mixer.Sound(buffer=_concat(
            _tone(880, 0.06, 0.2, "sine", 0.02),
            _tone(1320, 0.08, 0.18, "sine", 0.04),
        ))

        # Powerup collected - ascending chord
        self.collect_powerup = pygame.mixer.Sound(buffer=_concat(
            _tone(440, 0.07, 0.18, "triangle", 0.02),
            _tone(660, 0.07, 0.18, "triangle", 0.02),
            _tone(880, 0.1, 0.22, "triangle", 0.05),
        ))

        # Echo spawned - low ominous tone
        self.echo_spawn = pygame.mixer.Sound(buffer=_mix(
            _tone(110, 0.35, 0.12, "sine", 0.2),
            _tone(165, 0.25, 0.08, "sine", 0.15),
        ))

        # Ghost eaten - satisfying ascending pop
        self.ghost_eaten = pygame.mixer.Sound(buffer=_concat(
            _tone(300, 0.03, 0.25, "square", 0.01),
            _tone(600, 0.05, 0.2, "sine", 0.02),
            _tone(900, 0.07, 0.18, "sine", 0.04),
        ))

        # Game over - sad descending notes
        self.game_over = pygame.mixer.Sound(buffer=_concat(
            _tone(440, 0.2, 0.2, "triangle", 0.05),
            _tone(370, 0.2, 0.2, "triangle", 0.05),
            _tone(330, 0.2, 0.2, "triangle", 0.05),
            _tone(220, 0.45, 0.18, "triangle", 0.3),
        ))

    def _generate_music(self) -> None:
        """Generate a chill ambient background loop."""
        # C minor pentatonic for a moody, chill vibe
        # Melody notes (higher octave)
        C4, Eb4, F4, G4, Bb4 = 262, 311, 349, 392, 466
        C5 = 523

        # Bass notes (lower octave)
        C3, Eb3, F3, G3, Bb3 = 131, 156, 175, 196, 233

        note_len = 0.35
        gap = 0.05
        step = note_len + gap

        # Melody: gentle pentatonic arpeggio pattern (16 notes = ~6.4s loop)
        melody_seq = [
            C4, Eb4, G4, Bb4, G4, Eb4, F4, C4,
            Eb4, G4, Bb4, C5, Bb4, G4, F4, Eb4,
        ]

        melody_parts = []
        for freq in melody_seq:
            melody_parts.append(_tone(freq, note_len, 0.06, "triangle", 0.15))
            melody_parts.append(_silence(gap))
        melody = _concat(*melody_parts)

        # Bass: sustained notes, each spans 2 melody notes
        bass_seq = [C3, C3, Eb3, F3, C3, C3, G3, Eb3]
        bass_parts = []
        for freq in bass_seq:
            bass_parts.append(_tone(freq, step * 2, 0.05, "sine", 0.1))
        bass = _concat(*bass_parts)

        # Pad: very soft sustained chord tones for atmosphere
        total_dur = step * len(melody_seq)
        pad = _mix(
            _tone(C4, total_dur, 0.02, "sine", 0.5),
            _tone(Eb4, total_dur, 0.015, "sine", 0.5),
            _tone(G4, total_dur, 0.015, "sine", 0.5),
        )

        music_data = _mix(melody, bass, pad)
        self.music = pygame.mixer.Sound(buffer=music_data)

    def play_music(self) -> None:
        """Start background music loop."""
        if self.enabled:
            self.music.play(loops=-1)
            self.music.set_volume(0.35)

    def stop_music(self) -> None:
        """Stop background music."""
        if self.enabled:
            self.music.stop()

    def play(self, sound_name: str) -> None:
        """Play a sound effect by name.

        Args:
            sound_name: Name of the sound to play.
        """
        if not self.enabled:
            return
        sound = getattr(self, sound_name, None)
        if sound and isinstance(sound, pygame.mixer.Sound):
            sound.play()

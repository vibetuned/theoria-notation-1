"""Module 04 lessons (Gehrkens chs. VII-VIII): scales and keys.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/04-scales-and-keys/scenes.py TheMajorScaleRule -w -l
"""

from pathlib import Path

from manimlib import DOWN, ORIGIN, UP, FadeIn, FadeOut, Scene, Text, Transform, VGroup, Write

from theoria.core.examples import example_events, example_measures, load_example
from theoria.notation.score import EngravedScore, scroll_play
from theoria.theme import BLUE, HIGHLIGHT, INK, MUTED

BOOK = Path(__file__).resolve().parents[2] / "assets" / "book"


def _present(scene, filename, measures=None, seconds_per_quarter=0.5, height=2.8):
    """Engrave a book plate at readable size and play it: notes light at
    their onsets, and long systems scroll to follow the music."""
    xml = load_example(BOOK / filename)
    if measures is not None:
        xml = example_measures(xml, *measures)
    score = EngravedScore(xml)
    scroll_play(
        scene,
        score,
        events=example_events(xml, seconds_per_quarter=seconds_per_quarter),
        seconds_per_quarter=seconds_per_quarter,
        height=height,
    )
    return score


class TheMajorScaleRule(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Scales: a ladder with a pattern", font_size=40).to_edge(UP)
        self.play(Write(title))

        # {[2]} Checkpoint: C major from the book's fifteen-scale plate
        score = _present(
            self, "scales.musicxml", measures=(1, 2), seconds_per_quarter=0.45
        )
        caption = Text(
            "a scale is a ladder of tones, each loyal to one home tone: the tonic",
            font_size=25,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))
        self.wait(1.2)

        # {[3]} Checkpoint: the half-step positions
        for i in (2, 3, 6, 7):
            if i < len(score.note_ids):
                score.note(score.note_ids[i]).set_color(HIGHLIGHT)
        rule = Text(
            "major means: half steps between 3 and 4, and between 7 and 8 — nowhere else",
            font_size=24,
            color=HIGHLIGHT,
        )
        rule.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, rule))
        self.wait(1.8)

        # {[4]} Checkpoint: tetrachords — the same scale in fifteen positions
        tetra = Text(
            "each scale splits into two identical halves — and the upper half starts the next key",
            font_size=23,
            color=MUTED,
        )
        tetra.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, tetra))
        self.wait(2.2)


class TheThreeMinors(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Minor: one key, three shapes", font_size=40).to_edge(UP)
        self.play(Write(title))

        # {[2]} Checkpoint: the book's A minor plate, all three forms
        # three scale forms in one long system: readable height + scroll
        score = _present(self, "minor.musicxml", seconds_per_quarter=0.45)
        caption = Text(
            "minor begins with a smaller third: three half steps from 1 to 3",
            font_size=25,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))
        self.wait(1.0)

        # {[3]} Checkpoint: the three forms named
        forms = Text(
            "natural keeps the signature; harmonic raises 7; melodic raises 6 and 7 going up only",
            font_size=23,
            color=HIGHLIGHT,
        )
        forms.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, forms))
        self.wait(1.8)

        # {[4]} Checkpoint: relative minor
        relative = Text(
            "every signature serves two keys: a major, and its relative minor three degrees below",
            font_size=23,
            color=BLUE,
        )
        relative.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, relative))
        self.wait(1.6)

        # {[5]} Checkpoint: the raised seventh is an accidental
        accidental = Text(
            "the raised seventh never enters the signature — it arrives as an accidental, every time",
            font_size=23,
            color=MUTED,
        )
        accidental.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, accidental))
        self.wait(2.2)

"""Module 07 lessons (Gehrkens ch. XVII): intervals.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/07-intervals/scenes.py HearingIntervals -w -l
"""

from pathlib import Path

from manimlib import DOWN, UP, FadeIn, FadeOut, Scene, Text, Transform, Write

from theoria.core.examples import example_events, load_example
from theoria.notation.score import EngravedScore, scroll_play
from theoria.theme import BLUE, HIGHLIGHT, INK, MUTED

BOOK = Path(__file__).resolve().parents[2] / "assets" / "book"


def _present(scene, filename, seconds_per_quarter=0.5, height=2.8):
    xml = load_example(BOOK / filename)
    score = EngravedScore(xml)
    scroll_play(
        scene,
        score,
        events=example_events(xml, seconds_per_quarter=seconds_per_quarter),
        seconds_per_quarter=seconds_per_quarter,
        height=height,
    )
    return score


class HearingIntervals(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Intervals: together, or one after another", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "the same two tones, HARMONIC when sounded together, MELODIC in succession",
            font_size=23,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: harmonic vs melodic (figs. 62-63)
        score = _present(self, "fig62-63.musicxml", seconds_per_quarter=0.5)
        self.play(FadeOut(score))

        # {[3]} Checkpoint: intervals above the tonic (fig. 64)
        above = Text(
            "measured up from the tonic, every scale interval is MAJOR or PERFECT",
            font_size=24,
            color=BLUE,
        )
        above.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, above))
        _present(self, "fig64.musicxml", seconds_per_quarter=0.5)

        # {[4]} Checkpoint: the two-step naming method
        method = Text(
            "name in two steps: count staff degrees for the NUMBER, count half steps for the QUALITY",
            font_size=22,
            color=HIGHLIGHT,
        )
        method.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, method))
        self.wait(1.8)

        # {[5]} Checkpoint: the size ladder and inversion
        ladder = Text(
            "sizes order diminished < minor < major < augmented — and inversions sum to nine",
            font_size=23,
            color=MUTED,
        )
        ladder.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, ladder))
        self.wait(2.2)

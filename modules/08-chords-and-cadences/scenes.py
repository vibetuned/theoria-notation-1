"""Module 08 lessons (Gehrkens ch. XVIII): chords and cadences.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/08-chords-and-cadences/scenes.py TheFourCadences -w -l
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


class TheTriadFamily(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Triads: the chords with three tones", font_size=40).to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "a triad on every degree of the major key — the book's own figure",
            font_size=24,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: the major-key triads (fig. 65)
        score = _present(self, "fig65.musicxml", seconds_per_quarter=0.6)

        # {[3]} Checkpoint: the four qualities
        qualities = Text(
            "major: a major third with a minor on top — minor reverses them — two minors: diminished — two majors: augmented",
            font_size=20,
            color=HIGHLIGHT,
        )
        qualities.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, qualities))
        self.wait(1.8)

        # {[4]} Checkpoint: the minor-key triads
        self.play(FadeOut(score))
        minor = Text(
            "the same construction on the minor scale — the numerals sized by quality",
            font_size=24,
            color=BLUE,
        )
        minor.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, minor))
        _present(self, "triads.musicxml", seconds_per_quarter=0.6)

        # {[5]} Checkpoint: the common chords
        common = Text(
            "three do most of the work everywhere: I, IV, and V — the common chords",
            font_size=24,
            color=MUTED,
        )
        common.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, common))
        self.wait(2.2)


class TheFourCadences(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Cadences: how phrases end", font_size=40).to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "the AUTHENTIC cadence: V to I — the most direct close music has",
            font_size=24,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: authentic (fig. 68)
        score = _present(self, "fig68.musicxml", seconds_per_quarter=0.55)
        self.play(FadeOut(score))

        # {[3]} Checkpoint: plagal (fig. 69)
        plagal = Text(
            "the PLAGAL cadence: IV to I — the church close, the Amen",
            font_size=24,
            color=BLUE,
        )
        plagal.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, plagal))
        score = _present(self, "fig69.musicxml", seconds_per_quarter=0.55)
        self.play(FadeOut(score))

        # {[4]} Checkpoint: half (fig. 70)
        half = Text(
            "the HALF-CADENCE rests on V — a comma, not a period; it cannot end the piece",
            font_size=23,
            color=HIGHLIGHT,
        )
        half.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, half))
        score = _present(self, "fig70.musicxml", seconds_per_quarter=0.55)
        self.play(FadeOut(score))

        # {[5]} Checkpoint: deceptive (fig. 71)
        deceptive = Text(
            "and the DECEPTIVE cadence: V promises home and turns aside — most often to vi",
            font_size=23,
            color=HIGHLIGHT,
        )
        deceptive.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, deceptive))
        _present(self, "fig71.musicxml", seconds_per_quarter=0.55)

        # {[6]} Checkpoint: perfect vs imperfect
        perfect = Text(
            "root on top at the final chord: PERFECT — third or fifth on top: imperfect",
            font_size=24,
            color=MUTED,
        )
        perfect.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, perfect))
        self.wait(2.2)

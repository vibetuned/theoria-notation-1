"""Module 05 lessons (Gehrkens chs. IV, V, XIII): playing it right —
signs and expression.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/05-signs-and-expression/scenes.py DotsTiesSlurs -w -l
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


class DotsTiesSlurs(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Dots, ties, slurs: the connective tissue", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "the TIE joins two notes of one pitch into one sound — even across a barline",
            font_size=23,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: ties (figs. 30-31)
        score = _present(self, "fig30-31.musicxml", seconds_per_quarter=0.5)
        self.play(FadeOut(score))

        # {[3]} Checkpoint: the slur's four lives
        slur = Text(
            "the SLUR has four lives: legato, the phrase-mark, one syllable over many notes, the tuplet",
            font_size=22,
            color=HIGHLIGHT,
        )
        slur.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, slur))
        score = _present(self, "fig32-33.musicxml", seconds_per_quarter=0.5)

        # {[4]} Checkpoint: dot arithmetic
        dots = Text(
            "dot arithmetic: one dot makes 3/2 of the value, two make 7/4, three make 15/8",
            font_size=23,
            color=BLUE,
        )
        dots.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, dots))
        self.wait(1.8)

        # {[5]} Checkpoint: articulation marks
        marks = Text(
            "staccato dot, tenuto dash, accent wedge — how a note is LEFT matters as much as how it starts",
            font_size=21,
            color=MUTED,
        )
        marks.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, marks))
        self.wait(2.2)


class LoudSoftAndTheRoadmap(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Dynamics — and the roadmap signs", font_size=40).to_edge(UP)
        self.play(Write(title))

        # {[2]} Checkpoint: the dynamics ladder
        ladder = Text("ppp  pp  p  mp  mf  f  ff  fff", font_size=40, color=INK)
        ladder.move_to((0.0, 1.2, 0.0))
        caption = Text(
            "loudness is RELATIVE: the ladder orders it, the room and the piece decide it",
            font_size=23,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(ladder), FadeIn(caption))
        self.wait(1.6)

        # {[3]} Checkpoint: the three swells
        swells = Text(
            "sforzando strikes ONE tone; rinforzando lifts a passage at once; crescendo grows by degrees",
            font_size=22,
            color=HIGHLIGHT,
        )
        swells.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, swells))
        self.wait(1.8)

        # {[4]} Checkpoint: the repeat roadmap (figs. 25-27)
        self.play(FadeOut(ladder))
        roadmap = Text(
            "and the roadmap: repeat dots, first and second endings, D.C., D.S., fine — hear one in action",
            font_size=22,
            color=BLUE,
        )
        roadmap.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, roadmap))
        _present(self, "fig25-27.musicxml", seconds_per_quarter=0.5)

        # {[5]} Checkpoint: octave signs
        octaves = Text(
            "8va lifts a passage an octave, 8va bassa drops it, loco brings it home",
            font_size=23,
            color=MUTED,
        )
        octaves.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, octaves))
        self.wait(2.2)

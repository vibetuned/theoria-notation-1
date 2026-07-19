"""Module 01 lessons (Gehrkens chs. I-II): seeing music — the staff,
clefs, and note shapes.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/01-seeing-music/scenes.py SeeingTheStaff -w -l
"""

from pathlib import Path

from manimlib import DOWN, UP, FadeIn, Scene, Text, Transform, VGroup, Write

from theoria.core.examples import example_events, load_example
from theoria.notation.score import EngravedScore, scroll_play
from theoria.notation.staff import grand_staff_for, place_satb
from theoria.theme import BLUE, HIGHLIGHT, INK, MUTED

BOOK = Path(__file__).resolve().parents[2] / "assets" / "book"


class SeeingTheStaff(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("The staff: five lines, and a map of pitch", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))

        # {[2]} Checkpoint: the great staff appears
        staves, xs = grand_staff_for(3)
        self.play(Write(staves["treble"].lines), Write(staves["bass"].lines))
        caption = Text(
            "higher on the page is higher in pitch — every line and space is a DEGREE",
            font_size=24,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))
        self.wait(1.0)

        # {[3]} Checkpoint: the clefs assign the names
        self.play(
            Write(staves["treble"].clef("gClef")), Write(staves["bass"].clef("fClef"))
        )
        clefs = Text(
            "the G clef curls around G; the F clef's dots embrace F — clefs ASSIGN the names",
            font_size=23,
            color=HIGHLIGHT,
        )
        clefs.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, clefs))
        self.wait(1.4)

        # {[4]} Checkpoint: middle C joins the two staves
        heads, extras = place_satb(staves, ("C3", "C4"), xs[1], duration="whole")
        heads["C4"].set_color(HIGHLIGHT)
        great = Text(
            "between the two staves, on its own little line, lives MIDDLE C — the great staff's hinge",
            font_size=22,
            color=BLUE,
        )
        great.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(VGroup(extras, *heads.values())), Transform(caption, great))
        self.wait(1.6)

        # {[5]} Checkpoint: the promise
        promise = Text(
            "eleven lines, one hinge, two clefs: every note you will ever read lives here",
            font_size=23,
            color=MUTED,
        )
        promise.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, promise))
        self.wait(2.2)


class HowNotesAreDrawn(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("How notes are drawn", font_size=40).to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "head, stem, hook — and rules for which way each may point",
            font_size=25,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: the book's own notation figures
        xml = load_example(BOOK / "fig01.musicxml")
        score = EngravedScore(xml)
        scroll_play(
            self,
            score,
            events=example_events(xml, seconds_per_quarter=0.5),
            seconds_per_quarter=0.5,
            height=2.6,
        )

        # {[3]} Checkpoint: the stem rule
        stems = Text(
            "below the middle line, stems go UP on the right; above it, DOWN on the left",
            font_size=23,
            color=HIGHLIGHT,
        )
        stems.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, stems))
        self.wait(1.8)

        # {[4]} Checkpoint: beams and dots
        beams = Text(
            "eighths and shorter may share a BEAM; a dot always sits in a space, never on a line",
            font_size=23,
            color=MUTED,
        )
        beams.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, beams))
        self.wait(2.2)

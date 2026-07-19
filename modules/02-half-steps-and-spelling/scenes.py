"""Module 02 lessons (Gehrkens chs. II-III): half steps and spelling —
accidentals and key signatures.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/02-half-steps-and-spelling/scenes.py DegreeModifiers -w -l
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


class DegreeModifiers(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Sharps and flats: modifiers of the DEGREE", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "a sharp does not push a note up — it makes the staff degree MEAN a higher pitch",
            font_size=22,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: Rice's six alteration rules (figs. 18-23)
        score = _present(self, "fig18-23.musicxml", seconds_per_quarter=0.45)

        # {[3]} Checkpoint: the six rules in one breath
        rules = Text(
            "to raise: sharp a natural, double-sharp a sharp, natural a flat — mirror it all to lower",
            font_size=22,
            color=HIGHLIGHT,
        )
        rules.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, rules))
        self.wait(1.8)

        # {[4]} Checkpoint: the barline rule
        barline = Text(
            "an accidental lives to the END OF ITS MEASURE — the barline cancels it, unless a tie carries it over",
            font_size=21,
            color=BLUE,
        )
        barline.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, barline))
        self.wait(1.8)

        # {[5]} Checkpoint: enharmonics
        enharmonic = Text(
            "two spellings can share one sound — G sharp and A flat are ENHARMONIC twins",
            font_size=23,
            color=MUTED,
        )
        enharmonic.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, enharmonic))
        self.wait(2.2)


class ReadingSignatures(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Key signatures — and whose key it is", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "the signature sets its accidentals for the whole piece, once, at the clef",
            font_size=23,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: the major-or-minor test (figs. 12-13)
        score = _present(self, "fig12-13.musicxml", seconds_per_quarter=0.5)

        # {[3]} Checkpoint: the test
        test = Text(
            "every signature serves TWO keys — look at the final bass chord: DO-chord major, LA-chord minor",
            font_size=21,
            color=HIGHLIGHT,
        )
        test.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, test))
        self.wait(1.8)

        # {[4]} Checkpoint: where this goes
        onward = Text(
            "why those sharps arrive in that order is the scales' story — module four",
            font_size=23,
            color=MUTED,
        )
        onward.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, onward))
        self.wait(2.2)

"""Module 06 lessons (Gehrkens ch. VI): embellishments.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/06-ornaments/scenes.py TheOrnamentGallery -w -l
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


class TheOrnamentGallery(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Embellishments: small signs, many notes", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "the TRILL: rapid alternation with the diatonic neighbor above — sign, then sound",
            font_size=23,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: the trill realized (figs. 40-44)
        score = _present(self, "fig40.musicxml", seconds_per_quarter=0.4)
        self.play(FadeOut(score))

        # {[3]} Checkpoint: mordent and inverted mordent
        mordent = Text(
            "the MORDENT dips to the lower neighbor and back; inverted, it touches the upper",
            font_size=23,
            color=BLUE,
        )
        mordent.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, mordent))
        score = _present(self, "fig45-46.musicxml", seconds_per_quarter=0.4)
        self.play(FadeOut(score))

        # {[4]} Checkpoint: the turn
        turn = Text(
            "the TURN circles its note: upper neighbor, note, lower neighbor, note",
            font_size=24,
            color=HIGHLIGHT,
        )
        turn.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, turn))
        score = _present(self, "fig47.musicxml", seconds_per_quarter=0.4)

        # {[5]} Checkpoint: why they matter
        why = Text(
            "ornaments are waning, Gehrkens admits — but old music cannot be read without them",
            font_size=23,
            color=MUTED,
        )
        why.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, why))
        self.wait(2.2)


class TheLeaningNotes(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Appoggiatura and acciaccatura", font_size=40).to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "the APPOGGIATURA leans on the beat and takes real time from its note",
            font_size=24,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: the appoggiatura realized (figs. 48-49)
        score = _present(self, "fig48.musicxml", seconds_per_quarter=0.4)
        self.play(FadeOut(score))

        # {[3]} Checkpoint: the value rules
        rules = Text(
            "its worth by rule: half the plain note — two-thirds of a dotted one — a tied note's first value",
            font_size=22,
            color=HIGHLIGHT,
        )
        rules.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, rules))
        self.wait(1.8)

        # {[4]} Checkpoint: the acciaccatura
        crushed = Text(
            "the ACCIACCATURA — slashed stem — is crushed in with no time of its own, never accented",
            font_size=22,
            color=BLUE,
        )
        crushed.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, crushed))
        _present(self, "fig50-52.musicxml", seconds_per_quarter=0.4)
        self.wait(1.0)

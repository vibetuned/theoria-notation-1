"""Module 09 lessons (Gehrkens chs. XIV-XVI): how music is built — forms
and styles.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/09-form/scenes.py FormAndStyle -w -l
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


class FormAndStyle(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Form and style: the plan and the manner", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "a FUGUE is a form; COUNTERPOINT is a style — a plan versus a manner of building",
            font_size=22,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: a canon in action (fig. 57, Mozart)
        score = _present(self, "fig57.musicxml", seconds_per_quarter=0.45, height=3.2)

        # {[3]} Checkpoint: strict imitation
        canon = Text(
            "this is a CANON: one melody, strictly imitated — a round is a canon at the unison",
            font_size=22,
            color=HIGHLIGHT,
        )
        canon.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, canon))
        self.wait(1.8)

        # {[4]} Checkpoint: the two styles
        styles = Text(
            "two styles cover music: MONOPHONIC, one melody carried — POLYPHONIC, every voice a melody",
            font_size=22,
            color=BLUE,
        )
        styles.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, styles))
        self.wait(1.8)

        # {[5]} Checkpoint: the fugue's handshake
        fugue = Text(
            "the fugue imitates at the DOMINANT: the answer enters only after the subject completes",
            font_size=22,
            color=MUTED,
        )
        fugue.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, fugue))
        self.wait(2.2)


class PhraseToSonata(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("From phrase to sonata", font_size=40).to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "a PHRASE is about four measures; two phrases — question and answer — make a PERIOD",
            font_size=22,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: antecedent and consequent (fig. 58)
        score = _present(self, "fig58.musicxml", seconds_per_quarter=0.45)
        self.play(FadeOut(score))

        # {[3]} Checkpoint: the Ninth's theme as a song form
        theme = Text(
            "periods stack into SONG FORMS — Beethoven's Ninth carries its famous theme this way",
            font_size=22,
            color=HIGHLIGHT,
        )
        theme.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, theme))
        _present(self, "beethoven.musicxml", seconds_per_quarter=0.4, height=2.6)

        # {[4]} Checkpoint: sonata-form
        sonata = Text(
            "largest of all, SONATA-FORM: exposition, development, recapitulation — a drama in three acts",
            font_size=22,
            color=BLUE,
        )
        sonata.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, sonata))
        self.wait(1.8)

        # {[5]} Checkpoint: the listening course ends
        ending = Text(
            "rondo, suite, concerto, symphony — forms are maps: knowing them, you always know where you are",
            font_size=21,
            color=MUTED,
        )
        ending.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, ending))
        self.wait(2.2)

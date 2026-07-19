"""Module 03 lessons (Gehrkens chs. X-XII): time — beat, measure, tempo.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/03-time/scenes.py RhythmVersusMeasure -w -l
"""

from pathlib import Path

from manimlib import DOWN, UP, FadeIn, Scene, Text, Transform, Write

from theoria.core.examples import example_events, load_example
from theoria.notation.score import EngravedScore, scroll_play
from theoria.theme import BLUE, HIGHLIGHT, INK, MUTED

BOOK = Path(__file__).resolve().parents[2] / "assets" / "book"


class RhythmVersusMeasure(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Rhythm, measure, tempo: three different things", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "RHYTHM lives in the music itself; MEASURE is the grouping we adopt for it",
            font_size=23,
            color=INK,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: syncopation makes the difference audible (fig. 56)
        xml = load_example(BOOK / "fig56.musicxml")
        score = EngravedScore(xml)
        scroll_play(
            self,
            score,
            events=example_events(xml, seconds_per_quarter=0.5),
            seconds_per_quarter=0.5,
            height=2.6,
        )
        sync = Text(
            "accent a beat that usually goes unaccented and you hear SYNCOPATION",
            font_size=24,
            color=HIGHLIGHT,
        )
        sync.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, sync))
        self.wait(1.6)

        # {[3]} Checkpoint: simple and compound
        meters = Text(
            "duple and triple are SIMPLE; quadruple and sextuple COMPOUND them — accents mark the joints",
            font_size=22,
            color=BLUE,
        )
        meters.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, meters))
        self.wait(1.8)

        # {[4]} Checkpoint: C is a broken circle; tempo is the third thing
        tempo = Text(
            "the C signature is a broken circle, not a letter — and TEMPO is neither rhythm nor measure: it is speed",
            font_size=21,
            color=MUTED,
        )
        tempo.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, tempo))
        self.wait(2.2)


class TheTempoWords(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("Tempo: the ladder and its bends", font_size=40).to_edge(UP)
        self.play(Write(title))

        # {[2]} Checkpoint: the eight-group ladder
        ladder = Text(
            "grave · largo · larghetto · andante · moderato · allegro · vivace · presto",
            font_size=28,
            color=INK,
        )
        ladder.move_to((0.0, 1.2, 0.0))
        caption = Text(
            "eight families of speed, slow to fast — the metronome pins each in clicks per minute",
            font_size=23,
            color=BLUE,
        )
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(ladder), FadeIn(caption))
        self.wait(1.8)

        # {[3]} Checkpoint: gradual vs immediate change
        bends = Text(
            "ritardando and accelerando bend the tempo GRADUALLY; meno mosso and più mosso step it AT ONCE",
            font_size=22,
            color=HIGHLIGHT,
        )
        bends.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, bends))
        self.wait(1.8)

        # {[4]} Checkpoint: the word "time" retired
        reform = Text(
            "and say it Gehrkens' way: three-quarter MEASURE, andante TEMPO, dotted RHYTHM — never just \"time\"",
            font_size=21,
            color=MUTED,
        )
        reform.to_edge(DOWN, buff=0.8)
        self.play(Transform(caption, reform))
        self.wait(2.2)

"""Module 08 lessons (Gehrkens ch. XVIII): chords and cadences — the four
kinds of triad, the triads of a major and a minor key with their
numerals, then the four cadences one by one (in the exact voicings of the
module's cadence-bass exercise), perfect versus imperfect, and the same
cadences moved to G and F major, where the worksheets ask for the bass.

One idea per video; every word on screen comes from content/<lang>/.

Render (from the repo root):
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/08-chords-and-cadences/scenes.py AuthenticCadence -w -l
"""

import numpy as np
from manimlib import DOWN, LEFT, RIGHT, UP, Arrow, FadeIn, FadeOut, Rectangle, Transform, VGroup

from theoria.audio import add_events_sound, add_pitches_sound, add_sequence_sound
from theoria.exercises.rudiments import CADENCE_VOICINGS as _CADENCES  # the worksheet voicings, so videos and exercises agree
from theoria.notation.glyphs import SmuflGlyph
from theoria.notation.lesson import LessonScene, NoteRow, words
from theoria.notation.staff import signature_glyphs
from theoria.theme import BLUE, GREEN, HIGHLIGHT, INK, MUTED, ORANGE, RED

QUALITY_COLORS = {"major": HIGHLIGHT, "minor": BLUE, "diminished": RED, "augmented": GREEN}


def place(row: NoteRow, x: float, y: float) -> NoteRow:
    """Put a row's STAFF centre at (x, y), whatever the notes' range."""
    row.shift(np.array([x, y, 0.0]) - row.staff.get_center())
    return row


def split_list(text: str, sep: str = ",") -> list[str]:
    return [part.strip() for part in text.split(sep)]


def big(text: str, color=INK, size: float = 54):
    return words(text, size, color, weight="BOLD")


def tidy_accidentals(row: NoteRow, i: int):
    """Engravers' order in a chord: the highest accidental sits nearest the
    notes; lower ones move further left only where they would collide."""
    accidentals = [m for m in row.notes[i] if getattr(m, "glyph_name", "").startswith("accidental")]
    if len(accidentals) < 2:
        return
    step = 1.3 * row.staff.staff_space
    right = max(a.get_right()[0] for a in accidentals)
    columns: list[list] = []
    for acc in sorted(accidentals, key=lambda a: -a.get_center()[1]):
        k = 0
        while k < len(columns) and any(
            acc.get_bottom()[1] < b.get_top()[1] and acc.get_top()[1] > b.get_bottom()[1] for b in columns[k]
        ):
            k += 1
        if k == len(columns):
            columns.append([])
        columns[k].append(acc)
        acc.shift(RIGHT * (right - step * k - acc.get_right()[0]))


def heads(row: NoteRow, i: int) -> list[VGroup]:
    """A column's tones bottom to top, each with its ledger lines (and
    accidental, if any) — to reveal or colour one tone at a time."""
    parts = list(row.notes[i])
    tones, current = [], None
    for part in parts:
        if type(part).__name__ in ("Notehead", "NamedNotehead"):
            current = VGroup(part)
            tones.append(current)
        else:
            current.add(part)
    return tones


# ---------------------------------------------------------------------------
# Transposition for the G and F worksheets (letters + half steps), the same
# moves as the generator's _CADENCE_KEYS (C: P1, G: up a 5th, F: up a 4th)

_LETTERS = "CDEFGAB"
_NATURAL = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_MOVES = {"C": (0, 0), "G": (4, 7), "F": (3, 5)}


def _midi(p: str) -> int:
    accidental = p[1:-1]
    return 12 * (int(p[-1]) + 1) + _NATURAL[p[0]] + accidental.count("#") - accidental.count("-")


def moved(p: str, key: str) -> str:
    steps, semis = _MOVES[key]
    index = _LETTERS.index(p[0]) + steps
    letter, octave = _LETTERS[index % 7], int(p[-1]) + index // 7
    diff = _midi(p) + semis - (12 * (octave + 1) + _NATURAL[letter])
    return f"{letter}{'#' * diff if diff > 0 else '-' * -diff}{octave}"


def cadence_in(kind: str, key: str = "C"):
    """[(numeral, upper voices, bass), (numeral, upper, bass)] in `key`."""
    return [(roman, [moved(p, key) for p in upper], moved(bass, key)) for roman, upper, bass in _CADENCES[kind]]


# ---------------------------------------------------------------------------
# A grand staff of whole-note chords (upper voices treble, bass alone in the
# bass staff, keyboard style — the worksheets' layout)

_SIGNATURE_SIZE = {"C": 0, "G": 1, "F": -1}
_BASS_SIG_STEPS = {"#": (6, 3, 7, 4, 1, 5, 2), "-": (2, 5, 1, 4, 0, 3, -1)}


class GrandStaff(VGroup):
    def __init__(self, uppers, basses, x: float = -2.0, y: float = 1.75, staff_space: float = 0.3,
                 spacing: float = 13.0, gap_ss: float = 4.0, key: str = "C"):
        super().__init__()
        n = _SIGNATURE_SIZE[key]
        common = dict(
            staff_space=staff_space, spacing_ss=spacing, duration="whole",
            left_margin_ss=6.5 + 1.1 * abs(n), right_margin_ss=2.5, show_accidentals=n == 0,
        )
        self.treble = place(NoteRow(uppers, clef="treble", **common), x, y)
        self.bass = place(NoteRow(basses, clef="bass", **common), x, y - (4 + gap_ss) * staff_space)
        top, bottom = self.treble.staff.get_top()[1], self.bass.staff.get_bottom()[1]
        left = self.treble.staff.get_left()[0]
        line = Rectangle(width=0.03, height=top - bottom, fill_color=INK, fill_opacity=1.0, stroke_width=0)
        line.move_to(np.array([left, (top + bottom) / 2, 0.0]))
        brace = SmuflGlyph("brace", staff_space=staff_space)
        brace.stretch_to_fit_height(top - bottom).set_width(0.28, stretch=True)
        brace.move_to(np.array([left - 0.22, (top + bottom) / 2, 0.0]))
        self.frame = VGroup(self.treble.staff, self.treble.clef, self.bass.staff, self.bass.clef, line, brace)
        if n:
            self.frame.add(signature_glyphs(self.treble.staff, key, x_start=3.6))
            sign = "#" if n > 0 else "-"
            glyph_name = "accidentalSharp" if n > 0 else "accidentalFlat"
            for k in range(abs(n)):
                glyph = SmuflGlyph(glyph_name, staff_space=staff_space)
                self.bass.staff.place(glyph, 3.6 + 1.1 * k, _BASS_SIG_STEPS[sign][k])
                self.frame.add(glyph)
        self.add(self.frame)
        self.bass_colors = [INK] * len(basses)
        self.add(*(m for m in self.treble.notes + self.bass.notes if m is not None))

    def chord(self, i: int) -> VGroup:
        return VGroup(*(m for m in (self.treble.notes[i], self.bass.notes[i]) if m is not None))

    def x(self, i: int) -> float:
        return self.treble.note_x(i)

    def under(self, i: int, text: str, size: float = 44, color=INK):
        """A label (roman numeral) under the bass staff at chord i."""
        mob = big(text, color, size)
        mob.move_to(np.array([self.x(i), self.bass.staff.get_bottom()[1] - 0.55, 0.0]))
        return mob

    def light(self, i: int, color=HIGHLIGHT):
        self.chord(i).set_color(color)

    def restore(self, i: int):
        self.treble.notes[i].set_color(INK)
        if self.bass.notes[i] is not None:
            self.bass.notes[i].set_color(self.bass_colors[i])


def play_chords(scene, staff: GrandStaff, chords: list[list[str]], order=None, seconds: float = 1.3, last: float = 2.2):
    """Sound chords back to back, each lit while it sounds."""
    order = list(order if order is not None else range(len(chords)))
    events, t = [], 0.0
    durations = [seconds] * (len(order) - 1) + [last]
    for i, d in zip(order, durations):
        events.append((t, tuple(chords[i]), d))
        t += d
    add_events_sound(scene, events)
    for i, d in zip(order, durations):
        staff.light(i)
        scene.wait(d)
        staff.restore(i)


def right_panel(*mobs, x: float = 4.4, y: float = 0.45, buff: float = 0.35) -> VGroup:
    group = VGroup(*mobs).arrange(DOWN, buff=buff)
    group.move_to(np.array([x, y, 0.0]))
    return group


# ---------------------------------------------------------------------------
# 1. The four kinds of triad


_KINDS = (
    ("major", ["C4", "E4", "G4"]),
    ("minor", ["C4", "E-4", "G4"]),
    ("diminished", ["C4", "E-4", "G-4"]),
    ("augmented", ["C4", "E4", "G#4"]),
)


class FourKindsOfTriad(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a triad built tone by tone: root, third, fifth
        self.title()
        row = place(NoteRow([["C4", "E4", "G4"]], staff_space=0.55, duration="whole", right_margin_ss=0.6), -1.8, 0.9)
        tones = heads(row, 0)
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.5)
        self.caption("triad", wait=False)
        for tone, pitch, key in zip(tones, ("C4", "E4", "G4"), ("label-root", "label-third", "label-fifth")):
            label = words(self.t(key), 40, HIGHLIGHT)
            label.move_to(np.array([row.staff.get_right()[0] + 0.35 + label.get_width() / 2, tone[0].get_y(), 0.0]))
            self.play(FadeIn(tone, shift=DOWN * 0.15), FadeIn(label), run_time=0.4)
            add_pitches_sound(self, [pitch], duration=0.9)
            self.wait(1.1)
        add_pitches_sound(self, ["C4", "E4", "G4"], duration=1.6)
        self.wait(2.0)
        self.clear_stage()

        # {[2]} Checkpoint: four kinds on C, each made of two thirds
        row = place(
            NoteRow([p for _, p in _KINDS], staff_space=0.48, spacing_ss=6.4, duration="whole"), 0.0, 0.75
        )
        for i in range(len(_KINDS)):
            tidy_accidentals(row, i)
        names = row.labels_under([self.t(f"name-{kind}") for kind, _ in _KINDS], size=40)
        thirds = VGroup(*(
            words(self.t(f"thirds-{kind}"), 34, MUTED).move_to(np.array([row.note_x(i), row.staff.get_top()[1] + 0.5, 0.0]))
            for i, (kind, _) in enumerate(_KINDS)
        ))
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
        for i, (kind, pitches) in enumerate(_KINDS):
            color = QUALITY_COLORS[kind]
            self.caption(kind, wait=False)
            row.notes[i].set_color(color), names[i].set_color(color)
            self.play(FadeIn(row.notes[i]), FadeIn(names[i]), FadeIn(thirds[i]), run_time=0.4)
            add_sequence_sound(self, pitches, note_duration=1.0, qpm=200)
            self.wait(1.0)
            add_pitches_sound(self, pitches, duration=1.5)
            self.wait(2.4)

        # {[3]} Checkpoint: or measure root to top: the fifth
        fifths = VGroup(*(
            words(self.t(f"fifth-{kind}"), 34, QUALITY_COLORS[kind]).move_to(thirds[i])
            for i, (kind, _) in enumerate(_KINDS)
        ))
        self.caption("fifths", wait=False)
        self.play(FadeOut(thirds), FadeIn(fifths), run_time=0.6)
        for i, (_, pitches) in enumerate(_KINDS):
            add_pitches_sound(self, [pitches[0], pitches[2]], duration=0.9)
            self.play(fifths[i].animate.scale(1.2), run_time=0.25)
            self.wait(0.75)
            self.play(fifths[i].animate.scale(1 / 1.2), run_time=0.2)
        self.wait(1.5)

        # {[4]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 2-3. The triads of a key


def key_triads(scene: LessonScene, chords, kinds, numerals_text: str, y: float = 0.75, staff_space: float = 0.4):
    """Build the seven triads one by one, sounding each; returns the row
    and the (hidden) numerals coloured by kind."""
    row = place(NoteRow(chords, staff_space=staff_space, spacing_ss=4.0, duration="whole"), 0.0, y)
    numerals = row.labels_under(split_list(numerals_text), size=46)
    scene.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
    scene.caption("build", wait=False)
    for i, pitches in enumerate(chords):
        scene.play(FadeIn(row.notes[i], shift=UP * 0.1), run_time=0.3)
        add_pitches_sound(scene, pitches, duration=0.9)
        scene.wait(0.75)
    scene.wait(1.0)
    return row, numerals


_C_MAJOR = (
    ["C4", "E4", "G4"], ["D4", "F4", "A4"], ["E4", "G4", "B4"], ["F4", "A4", "C5"],
    ["G4", "B4", "D5"], ["A4", "C5", "E5"], ["B4", "D5", "F5"],
)
_C_KINDS = ("major", "minor", "minor", "major", "major", "minor", "diminished")

# Gehrkens builds the minor-key triads on the harmonic form (p. 88)
_A_MINOR = (
    ["A3", "C4", "E4"], ["B3", "D4", "F4"], ["C4", "E4", "G#4"], ["D4", "F4", "A4"],
    ["E4", "G#4", "B4"], ["F4", "A4", "C5"], ["G#4", "B4", "D5"],
)
_A_KINDS = ("minor", "diminished", "augmented", "minor", "major", "major", "diminished")


class TriadsOfAMajorKey(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a triad on every degree of C major
        self.title()
        row, numerals = key_triads(self, _C_MAJOR, _C_KINDS, self.t("numeral-list"))

        # {[2]} Checkpoint: Roman numerals: degree and kind at once
        self.caption("numerals", wait=False)
        self.play(FadeIn(numerals, lag_ratio=0.1), run_time=0.8)
        self.wait(2.5)
        self.caption("sizes", wait=False)
        self.play(
            *(numerals[i].animate.set_color(QUALITY_COLORS[k]) for i, k in enumerate(_C_KINDS)),
            *(row.notes[i].animate.set_color(QUALITY_COLORS[k]) for i, k in enumerate(_C_KINDS)),
            run_time=0.6,
        )
        self.wait(4.0)

        # {[3]} Checkpoint: I, IV and V — the common chords
        self.caption("common", wait=False)
        primary = (0, 3, 4)
        self.play(
            *(VGroup(row.notes[i], numerals[i]).animate.set_opacity(0.25) for i in range(7) if i not in primary),
            *(numerals[i].animate.scale(1.25) for i in primary),
            run_time=0.5,
        )
        events = [(t * 1.0, tuple(_C_MAJOR[i]), 1.0 if t < 3 else 1.8) for t, i in enumerate((0, 3, 4, 0))]
        add_events_sound(self, events)
        for i in (0, 3, 4, 0):
            row.notes[i].scale(1.15)
            self.wait(1.0)
            row.notes[i].scale(1 / 1.15)
        self.wait(2.5)

        # {[4]} Checkpoint: remember
        self.remember()


class TriadsOfAMinorKey(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a triad on every degree of A minor (harmonic form)
        self.title()
        row, numerals = key_triads(self, _A_MINOR, _A_KINDS, self.t("numeral-list"), y=0.95)

        # {[2]} Checkpoint: the numerals and their kinds
        self.caption("numerals", wait=False)
        self.play(
            FadeIn(numerals, lag_ratio=0.1),
            *(numerals[i].animate.set_color(QUALITY_COLORS[k]) for i, k in enumerate(_A_KINDS)),
            *(row.notes[i].animate.set_color(QUALITY_COLORS[k]) for i, k in enumerate(_A_KINDS)),
            run_time=0.8,
        )
        self.wait(3.5)

        # {[3]} Checkpoint: ii° and vii° diminished, III+ augmented
        self.caption("odd", wait=False)
        for i in (1, 6, 2):
            self.play(numerals[i].animate.scale(1.25), run_time=0.3)
            add_pitches_sound(self, _A_MINOR[i], duration=1.0)
            self.wait(1.0)
            self.play(numerals[i].animate.scale(1 / 1.25), run_time=0.2)
        self.wait(1.0)

        # {[4]} Checkpoint: the raised seventh makes V major: V to i
        self.caption("dominant", wait=False)
        sharps = [part for i in (2, 4, 6) for part in row.notes[i] if type(part).__name__ == "SmuflGlyph"]
        self.play(*(glyph.animate.scale(1.3) for glyph in sharps), run_time=0.4)
        self.play(*(glyph.animate.scale(1 / 1.3) for glyph in sharps), run_time=0.3)
        add_events_sound(self, [(0.0, tuple(_A_MINOR[4]), 1.2), (1.2, ("A3", "C4", "E4"), 2.0)])
        for i, d in ((4, 1.2), (0, 2.0)):
            row.notes[i].scale(1.1)
            self.wait(d)
            row.notes[i].scale(1 / 1.1)
        self.wait(1.5)

        # {[5]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 4-7. The four cadences, in the worksheet voicings


class CadenceLesson(LessonScene):
    """Shared shape: the two chords, each named, the bass motion, the name."""

    kind = "authentic"

    def show_cadence(self, key: str = "C"):
        pair = cadence_in(self.kind, key)
        self.chords = [[bass] + upper for _, upper, bass in pair]
        self.gs = GrandStaff([upper for _, upper, _ in pair], [bass for _, _, bass in pair], key=key)
        self.numerals = VGroup(*(self.gs.under(i, numeral) for i, (numeral, _, _) in enumerate(pair)))
        return pair

    def lesson(self):
        # {[1]} Checkpoint: title; the last two chords of a phrase, heard
        self.title()
        self.show_cadence()
        gs = self.gs
        self.play(FadeIn(gs), run_time=0.6)
        self.caption("cadence", wait=False)
        self.wait(0.6)
        play_chords(self, gs, self.chords)
        self.wait(1.0)

        # {[2]} Checkpoint: the first chord and its numeral
        self.caption("first", wait=False)
        self.play(FadeIn(self.numerals[0]), run_time=0.4)
        play_chords(self, gs, self.chords, order=[0], last=2.0)
        self.wait(1.5)

        # {[3]} Checkpoint: the second chord and its numeral
        self.caption("second", wait=False)
        self.play(FadeIn(self.numerals[1]), run_time=0.4)
        play_chords(self, gs, self.chords, order=[1], last=2.0)
        self.wait(1.5)

        # {[4]} Checkpoint: the bass motion, alone and in the cadence
        self.caption("bass", wait=False)
        gs.bass_colors = [BLUE, BLUE]
        gs.restore(0), gs.restore(1)
        a, b = gs.bass.notes[0][0], gs.bass.notes[1][0]
        arrow = Arrow(a.get_right(), b.get_left(), buff=0.18, fill_color=BLUE, thickness=5)
        self.play(FadeIn(arrow), run_time=0.4)
        basses = [self.chords[0][0], self.chords[1][0]]
        add_sequence_sound(self, basses, note_duration=1.0, qpm=70)
        for i in (0, 1):
            gs.bass.notes[i].set_color(HIGHLIGHT)
            self.wait(0.86)
            gs.bass.notes[i].set_color(BLUE)
        self.wait(0.8)
        play_chords(self, gs, self.chords)
        self.wait(0.8)

        # {[5]} Checkpoint: the cadence's name and formula
        formula = right_panel(big(self.t("formula"), HIGHLIGHT, 64), words(self.t("name"), 38, INK))
        self.caption("named", wait=False)
        self.play(FadeIn(formula, shift=LEFT * 0.2), run_time=0.5)
        play_chords(self, gs, self.chords)
        self.wait(1.5)


class AuthenticCadence(CadenceLesson):
    kind = "authentic"

    def construct(self):
        self.lesson()
        # {[6]} Checkpoint: remember
        self.remember()


class PlagalCadence(CadenceLesson):
    kind = "plagal"

    def construct(self):
        self.lesson()
        # {[6]} Checkpoint: remember
        self.remember()


class HalfCadence(CadenceLesson):
    kind = "half"

    def construct(self):
        self.lesson()
        # {[6]} Checkpoint: remember
        self.remember()


class DeceptiveCadence(CadenceLesson):
    kind = "deceptive"

    def construct(self):
        self.lesson()
        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 8. Perfect or imperfect: the soprano of the final chord (fig. 68)

# V to I three ways, the book's fig. 68 upper voices over the worksheet bass
_SOPRANO_WAYS = (
    (("D4", "G4", "B4"), ("E4", "G4", "C5")),  # root on top: perfect
    (("G4", "B4", "D5"), ("G4", "C5", "E5")),  # third on top: imperfect
    (("B4", "D5", "G5"), ("C5", "E5", "G5")),  # fifth on top: imperfect
)


class PerfectOrImperfect(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; an authentic cadence, the top voice in view
        self.title()
        tones = split_list(self.t("tones"))
        verdicts = split_list(self.t("verdicts"))
        numerals = split_list(self.t("numerals"))
        caption_keys = ("root", "third", "fifth")
        shown, first = None, None
        for way, ((v_upper, i_upper), tone, verdict, key) in enumerate(zip(_SOPRANO_WAYS, tones, verdicts, caption_keys)):
            # {[2]} Checkpoint: one way to voice it — which tone is on top?
            gs = GrandStaff([list(v_upper), list(i_upper)], ["G2", "C3"])
            labels = VGroup(gs.under(0, numerals[0]), gs.under(1, numerals[1]))
            chords = [["G2", *v_upper], ["C3", *i_upper]]
            if shown is None:
                self.play(FadeIn(gs), FadeIn(labels), run_time=0.6)
                self.caption("watch", wait=False)
            else:
                self.play(FadeOut(shown), FadeIn(gs), FadeIn(labels), run_time=0.6)
            play_chords(self, gs, chords)
            soprano = heads(gs.treble, 1)[-1]
            color = GREEN if way == 0 else ORANGE
            soprano.set_color(color)
            panel = right_panel(words(tone, 38, INK), big(verdict, color, 58), y=0.5)
            self.caption(key, wait=False)
            self.play(FadeIn(panel, shift=LEFT * 0.2), soprano.animate.scale(1.25), run_time=0.5)
            self.play(soprano.animate.scale(1 / 1.25), run_time=0.3)
            add_events_sound(self, [(0.0, tuple(chords[0]), 1.0), (1.0, tuple(chords[1]), 1.8)])
            self.wait(3.6)
            shown = VGroup(gs, labels, panel)
            if first is None:
                first = (shown, gs, chords)

        # {[3]} Checkpoint: back to the root on top: the most final close
        group, gs, chords = first
        self.play(FadeOut(shown), FadeIn(group), run_time=0.6)
        self.caption("final", wait=False)
        add_events_sound(self, [(0.0, tuple(chords[0]), 1.2), (1.2, tuple(chords[1]), 2.4)])
        self.wait(5.0)

        # {[4]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 9. The worksheets' keys: the missing bass in G and F major

_EXAMPLES = (("authentic", "G", 1), ("deceptive", "G", 1), ("plagal", "F", 0), ("half", "F", 1))


class CadencesInGAndF(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title
        self.title()
        shown = None
        for n, (kind, key, missing) in enumerate(_EXAMPLES, start=1):
            # {[2]} Checkpoint: a cadence in G or F with one bass note missing, then supplied
            pair = cadence_in(kind, key)
            chords = [[bass] + upper for _, upper, bass in pair]
            gs = GrandStaff([upper for _, upper, _ in pair], [bass for _, _, bass in pair], key=key)
            numerals = VGroup(*(gs.under(i, numeral) for i, (numeral, _, _) in enumerate(pair)))
            key_name, name, formula, question, answer = split_list(self.t(f"example-{n}"), "|")
            panel = right_panel(
                big(key_name, INK, 44), words(name, 34, MUTED), big(formula, HIGHLIGHT, 52), big(question, BLUE, 52),
                buff=0.3,
            )
            answer_mob = big(answer, BLUE, 52).move_to(panel[3])
            hidden = gs.bass.notes[missing]
            gs.remove(hidden)
            if shown is None:
                self.play(FadeIn(gs), FadeIn(numerals), FadeIn(panel), run_time=0.6)
                self.caption("worksheet")
            else:
                self.play(FadeOut(shown), FadeIn(gs), FadeIn(numerals), FadeIn(panel), run_time=0.6)
            self.caption(f"ask-{n}", wait=False)
            numerals[missing].set_color(BLUE)
            self.wait(3.5)
            # {[3]} Checkpoint: the root appears in the bass, and the cadence sounds
            hidden.set_color(BLUE)
            gs.bass_colors[missing] = BLUE
            self.play(FadeIn(hidden, scale=1.3), Transform(panel[3], answer_mob), run_time=0.5)
            gs.add(hidden)
            self.caption(f"answer-{n}", wait=False)
            play_chords(self, gs, chords)
            self.wait(1.2)
            shown = VGroup(gs, numerals, panel)

        # {[4]} Checkpoint: remember
        self.remember()

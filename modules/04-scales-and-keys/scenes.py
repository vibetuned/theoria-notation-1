"""Module 04 lessons (Gehrkens chs. VII-VIII): scales and keys.

The major scale's one pattern and its two matching tetrachords; then the
fifteen major keys, each drawn twice — the key signature on a staff above,
the same scale spelled with accidentals below — and every note sounded;
the enharmonic pairs; the minor scale's smaller third; its three forms on
A; and a tour of the minor keys in those three forms.

One idea per video; every word on screen comes from content/<lang>/.

Render (from the repo root):
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/04-scales-and-keys/scenes.py SharpMajors -w -l
"""

import numpy as np
from manimlib import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Line, ReplacementTransform, Transform, VGroup

from theoria.audio import add_pitches_sound, add_sequence_sound
from theoria.notation.lesson import (
    LABEL_SIZE,
    Keyboard,
    LessonScene,
    NoteRow,
    scale_pitches,
    step_marks,
    words,
)
from theoria.notation.staff import Staff, signature_glyphs
from theoria.theme import BLUE, GREEN, HIGHLIGHT, INK, MUTED, RED

# Gehrkens' fifteen positions of the one major scale (sec. 83) and their
# relative minors (sec. 88): signature size, + sharps / - flats
SIGNATURES = {
    "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
    "F": -1, "B-": -2, "E-": -3, "A-": -4, "D-": -5, "G-": -6, "C-": -7,
    "a": 0, "e": 1, "b": 2, "f#": 3, "c#": 4, "g#": 5, "d#": 6, "a#": 7,
    "d": -1, "g": -2, "c": -3, "f": -4, "b-": -5, "e-": -6, "a-": -7,
}
SHARP_ORDER, FLAT_ORDER = "FCGDAEB", "BEADGCF"


def signature_letters(key: str) -> tuple[str, str]:
    """(letters in signature order, '#' or '-') for a key."""
    n = SIGNATURES[key]
    return (SHARP_ORDER[:n], "#") if n >= 0 else (FLAT_ORDER[: -n], "-")


def raised(pitch: str) -> str:
    """A half step up, same letter: G4 -> G#4, B-4 -> B4, F#4 -> F##4."""
    letter, accidental, octave = pitch[0], pitch[1:-1], pitch[-1]
    up = {"": "#", "#": "##", "-": "", "--": "-"}[accidental]
    return f"{letter}{up}{octave}"


def scale_of(key: str, form: str = "primitive") -> list[str]:
    """Eight tones up from the tonic (octave 4), spelled from the
    signature; minor forms raise 7 (harmonic) or 6 and 7 (melodic up)."""
    letters, sign = signature_letters(key)
    pitches = scale_pitches(key[0].upper(), 4, {letter: sign for letter in letters})
    if form in ("harmonic", "melodic"):
        pitches[6] = raised(pitches[6])
    if form == "melodic":
        pitches[5] = raised(pitches[5])
    return pitches


def split_list(text: str) -> list[str]:
    """Content lists are comma-separated ('C major, G major, ...')."""
    return [part.strip() for part in text.split(",")]


def place(row: NoteRow, x: float, y: float) -> NoteRow:
    """Put a row's STAFF centre at (x, y) — centring the whole group would
    move the staff whenever the notes' range changes."""
    row.shift(np.array([x, y, 0.0]) - row.staff.get_center())
    return row


def row_of(pitches, y: float = 0.9, staff_space: float = 0.4, spacing: float = 3.4, duration: str = "whole") -> NoteRow:
    row = NoteRow(pitches, staff_space=staff_space, spacing_ss=spacing, duration=duration)
    return place(row, 0.0, y)


def sound_row(scene, row: NoteRow, pitches: list[str], seconds: float = 0.45, order=None, keyboard=None, after=None):
    """Sound the notes, lighting each as it plays. `after(i)` returns the
    colour note i keeps afterwards (default ink)."""
    order = list(order if order is not None else range(len(pitches)))
    add_sequence_sound(scene, [pitches[i] for i in order], note_duration=1.0, qpm=60 / seconds)
    for i in order:
        row.notes[i].set_color(HIGHLIGHT)
        if keyboard is not None:
            keyboard.press(pitches[i])
        scene.wait(seconds)
        row.notes[i].set_color(after(i) if after else INK)
        if keyboard is not None:
            keyboard.release(pitches[i])


def bracket(x0: float, x1: float, y: float, text: str, color=BLUE, below: bool = True, size: float = LABEL_SIZE) -> VGroup:
    """A square bracket from x0 to x1 with its label (under or over it)."""
    tick = 0.18 if below else -0.18
    line = VGroup(
        Line(np.array([x0, y + tick, 0]), np.array([x0, y, 0])),
        Line(np.array([x0, y, 0]), np.array([x1, y, 0])),
        Line(np.array([x1, y, 0]), np.array([x1, y + tick, 0])),
    ).set_stroke(color, width=4)
    label = words(text, size, color)
    label.next_to(line, DOWN if below else UP, buff=0.15)
    return VGroup(line, label)


# ---------------------------------------------------------------------------
# 1. The major scale: one pattern


class TheMajorPattern(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; C major on the staff and the keyboard
        self.title()
        pitches = scale_of("C")
        row = row_of(pitches, y=1.2)
        numbers = row.labels_under([str(i + 1) for i in range(8)], color=MUTED)
        keyboard = Keyboard("C4", "D5", white_width=0.8, height=1.1)
        keyboard.move_to(np.array([0.0, -1.68, 0.0]))
        self.play(FadeIn(row), FadeIn(numbers), FadeIn(keyboard), run_time=0.6)
        self.caption("climb", wait=False)
        sound_row(self, row, pitches, keyboard=keyboard)
        self.wait(1.2)

        # {[2]} Checkpoint: the steps between neighbours, one by one
        marks = step_marks(row, pitches)
        self.caption("steps", wait=False)
        for i, mark in enumerate(marks):
            keyboard.press(pitches[i], MUTED), keyboard.press(pitches[i + 1], MUTED)
            self.play(FadeIn(mark, shift=DOWN * 0.1), run_time=0.3)
            add_sequence_sound(self, pitches[i : i + 2], note_duration=1.0, qpm=160)
            self.wait(0.55)
            keyboard.release(pitches[i]), keyboard.release(pitches[i + 1])
        self.wait(1.0)

        # {[3]} Checkpoint: the two half steps, 3-4 and 7-8
        self.caption("halves", wait=False)
        for i in (2, 6):
            self.play(
                marks[i].animate.scale(1.3),
                numbers[i].animate.set_color(HIGHLIGHT),
                numbers[i + 1].animate.set_color(HIGHLIGHT),
                row.notes[i].animate.set_color(HIGHLIGHT),
                row.notes[i + 1].animate.set_color(HIGHLIGHT),
                run_time=0.4,
            )
            keyboard.press(pitches[i]), keyboard.press(pitches[i + 1])
            add_sequence_sound(self, pitches[i : i + 2], note_duration=1.0, qpm=90)
            self.wait(1.8)
            keyboard.release(pitches[i]), keyboard.release(pitches[i + 1])
        self.wait(1.5)
        for i in (2, 3, 6, 7):
            row.notes[i].set_color(INK)

        # {[4]} Checkpoint: the same pattern from D needs F sharp and C sharp
        d_pitches = scale_of("D")
        d_row = row_of(d_pitches, y=1.2)
        d_marks = step_marks(d_row, d_pitches)
        self.caption("on-d", wait=False)
        self.play(
            ReplacementTransform(VGroup(*row.notes), VGroup(*d_row.notes)),
            ReplacementTransform(marks, d_marks),
            run_time=0.8,
        )
        for i in (2, 6):  # F sharp and C sharp
            d_row.notes[i].set_color(BLUE)
        sound_row(self, d_row, d_pitches, keyboard=keyboard, after=lambda i: BLUE if i in (2, 6) else INK)
        self.wait(2.0)

        # {[5]} Checkpoint: one scale, many positions
        self.caption("one-scale", extra=0.5)

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 2. Tetrachords: two matching halves


class Tetrachords(LessonScene):
    def halves(self, row: NoteRow, y: float, lower_key: str = "lower", upper_key: str = "upper") -> VGroup:
        """Brackets under notes 1-4 and 5-8."""
        pad = 0.35
        return VGroup(
            bracket(row.note_x(0) - pad, row.note_x(3) + pad, y, self.t(lower_key), size=38),
            bracket(row.note_x(4) - pad, row.note_x(7) + pad, y, self.t(upper_key), size=38),
        )

    def construct(self):
        # {[1]} Checkpoint: title; C major in two halves of four
        self.title()
        pitches = scale_of("C")
        row = row_of(pitches, y=0.55, duration="quarter")
        marks = step_marks(row, pitches)
        marks[3].set_color(MUTED)
        y_bracket = row.staff.get_bottom()[1] - 0.75
        brackets = self.halves(row, y_bracket)
        self.play(FadeIn(row), run_time=0.5)
        sound_row(self, row, pitches)
        self.caption("split", wait=False)
        self.play(FadeIn(brackets), run_time=0.6)
        self.wait(2.5)

        # {[2]} Checkpoint: both halves climb whole, whole, half
        self.caption("same-steps", wait=False)
        self.play(FadeIn(VGroup(*marks[:3])), run_time=0.4)
        sound_row(self, row, pitches, order=range(4), seconds=0.5)
        self.play(FadeIn(VGroup(*marks[4:])), run_time=0.4)
        sound_row(self, row, pitches, order=range(4, 8), seconds=0.5)
        self.wait(0.8)
        self.caption("joined", wait=False)
        self.play(FadeIn(marks[3]), run_time=0.4)
        add_sequence_sound(self, pitches[3:5], note_duration=1.0, qpm=90)
        self.wait(2.6)

        # {[3]} Checkpoint: the upper half of C begins G major
        self.caption("sharp-chain", wait=False)
        shift = row.note_x(0) - row.note_x(4)
        self.play(
            FadeOut(VGroup(*row.notes[:4])),
            FadeOut(marks),
            FadeOut(brackets),
            *(row.notes[i].animate.shift(RIGHT * shift).set_color(BLUE) for i in range(4, 8)),
            run_time=1.0,
        )
        g_pitches = scale_of("G")
        g_row = row_of(g_pitches, y=0.55, duration="quarter")
        g_marks = step_marks(g_row, g_pitches)
        self.play(FadeIn(VGroup(*g_row.notes[4:])), run_time=0.5)
        self.wait(1.5)

        # {[4]} Checkpoint: its new upper half needs F sharp
        self.caption("f-sharp", wait=False)
        g_row.notes[6].set_color(HIGHLIGHT)
        self.play(FadeIn(VGroup(*g_marks[4:])), g_row.notes[6].animate.scale(1.2), run_time=0.5)
        self.play(g_row.notes[6].animate.scale(1 / 1.2), run_time=0.3)
        add_sequence_sound(self, g_pitches[4:], note_duration=1.0, qpm=110)
        self.wait(3.0)
        # the moved notes are G major's own lower half now
        for i in range(4):
            g_row.notes[i].set_color(BLUE)
            self.remove(row.notes[4 + i])
            self.add(g_row.notes[i])
        g_row.notes[6].set_color(BLUE)
        self.play(FadeIn(VGroup(*g_marks[:4])), run_time=0.4)
        sound_row(self, g_row, g_pitches, after=lambda i: BLUE if i == 6 else INK)
        self.wait(1.5)
        self.play(FadeOut(VGroup(*g_row.notes)), FadeOut(g_marks), run_time=0.5)

        # {[5]} Checkpoint: flat keys — C's lower half ends F major
        c_row = row_of(pitches, y=0.55, duration="quarter")
        self.play(FadeIn(VGroup(*c_row.notes)), run_time=0.4)
        self.caption("flat-chain", wait=False)
        f_pitches = scale_of("F")
        f_row = row_of(f_pitches, y=0.55, duration="quarter")
        f_marks = step_marks(f_row, f_pitches)
        self.play(
            FadeOut(VGroup(*c_row.notes[4:])),
            *(Transform(c_row.notes[i], f_row.notes[4 + i].copy().set_color(BLUE)) for i in range(4)),
            run_time=1.0,
        )
        self.wait(1.2)
        self.caption("b-flat", wait=False)
        f_row.notes[3].set_color(HIGHLIGHT)
        self.play(FadeIn(VGroup(*f_row.notes[:4])), FadeIn(VGroup(*f_marks[:3])), run_time=0.5)
        add_sequence_sound(self, f_pitches[:4], note_duration=1.0, qpm=110)
        self.wait(3.0)
        for i in range(4):
            f_row.notes[4 + i].set_color(BLUE)
            self.remove(c_row.notes[i])
            self.add(f_row.notes[4 + i])
        f_row.notes[3].set_color(BLUE)
        self.play(FadeIn(VGroup(*f_marks[3:])), run_time=0.4)
        sound_row(self, f_row, f_pitches, after=lambda i: BLUE if i == 3 else INK)
        self.wait(1.5)

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 3-4. The major keys, written two ways (Pedro's design: signature above,
# the same scale spelled with accidentals below, every note sounded)

SIG_STAFF_SPACE = 0.34
SCALE_STAFF_SPACE = 0.36
SIG_Y, SCALE_Y = 1.5, -0.95
TOUR_SPACING = 4.0  # room for an accidental between two whole notes
TOUR_MARGIN = 6.2  # first note: its accidental clears the clef


class KeyTour(LessonScene):
    """Shared machinery of the four key tours."""

    def stage(self):
        """The two empty staves that stay up for the whole tour."""
        sig_staff = Staff(width_ss=12.6, staff_space=SIG_STAFF_SPACE)
        sig_staff.move_to(np.array([-2.9, SIG_Y, 0.0]))
        sig_clef = sig_staff.clef("gClef", x_ss=0.8)
        scale_row = place(self.scale_row([None], left_margin_ss=TOUR_MARGIN + 7 * TOUR_SPACING), 0.0, SCALE_Y)
        self.sig_staff = sig_staff
        self.scale_staff = VGroup(scale_row.staff, scale_row.clef)
        self.play(FadeIn(VGroup(sig_staff, sig_clef)), FadeIn(self.scale_staff), run_time=0.6)
        self.shown = []

    def key_view(self, key: str, name: str, count: str, pitches: list[str]):
        """Signature glyphs, key name, count line and the scale's notes."""
        glyphs = signature_glyphs(self.sig_staff, key, x_start=3.6)
        name_mob = words(name, 46, INK, weight="BOLD")
        name_mob.move_to(np.array([self.sig_staff.get_right()[0] + 0.6, SIG_Y + 0.38, 0.0]), aligned_edge=LEFT)
        count_mob = words(count, 32, MUTED)
        count_mob.move_to(np.array([name_mob.get_left()[0], SIG_Y - 0.42, 0.0]), aligned_edge=LEFT)
        row = place(self.scale_row(pitches), 0.0, SCALE_Y)
        return glyphs, name_mob, count_mob, row

    @staticmethod
    def scale_row(pitches, left_margin_ss: float = None) -> NoteRow:
        return NoteRow(
            pitches, staff_space=SCALE_STAFF_SPACE, spacing_ss=TOUR_SPACING, duration="whole",
            left_margin_ss=left_margin_ss or TOUR_MARGIN, right_margin_ss=1.5,
        )

    def swap_in(self, *mobs, run_time: float = 0.5):
        """Fade the previous key's mobjects out and these in."""
        if self.shown:
            self.play(FadeOut(VGroup(*self.shown)), FadeIn(VGroup(*mobs)), run_time=run_time)
        else:
            self.play(FadeIn(VGroup(*mobs)), run_time=run_time)
        self.shown = list(mobs)

    def sound_linked(self, key: str, row: NoteRow, pitches: list[str], glyphs: VGroup, seconds: float, keep: dict | None = None):
        """Play the scale; each note carrying a signature accidental lights
        its twin in the signature (both stay blue)."""
        letters, sign = signature_letters(key)
        add_sequence_sound(self, pitches, note_duration=1.0, qpm=60 / seconds)
        for i, pitch in enumerate(pitches):
            row.notes[i].set_color(HIGHLIGHT)
            linked = pitch[0] in letters and pitch[1:-1] == sign
            if linked:
                glyphs[letters.index(pitch[0])].set_color(BLUE)
            self.wait(seconds)
            row.notes[i].set_color((keep or {}).get(i, INK))
            if linked:
                row.notes[i][2].set_color(BLUE)

    def show_major(self, key: str, name: str, count: str):
        pitches = scale_of(key)
        glyphs, name_mob, count_mob, row = self.key_view(key, name, count, pitches)
        self.swap_in(glyphs, name_mob, count_mob, *row.notes)
        return key, row, pitches, glyphs

    def play_major(self, view, seconds: float = 0.42, hold: float = 0.9):
        key, row, pitches, glyphs = view
        self.sound_linked(key, row, pitches, glyphs, seconds)
        self.wait(hold)

    def major_key(self, key: str, name: str, count: str, seconds: float = 0.42, hold: float = 0.9):
        view = self.show_major(key, name, count)
        self.wait(0.3)
        self.play_major(view, seconds, hold)

    def minor_key(self, key: str, name: str, count: str, forms: list[str], seconds: float = 0.25):
        """Primitive, then harmonic (7 raised), then melodic (6 and 7)."""
        pitches = scale_of(key)
        glyphs, name_mob, count_mob, row = self.key_view(key, name, count, pitches)
        tag = words(forms[0], 36, GREEN, weight="BOLD")
        tag.move_to(np.array([6.3, SIG_Y + 0.38, 0.0]), aligned_edge=RIGHT)
        self.swap_in(glyphs, name_mob, count_mob, *row.notes, tag)
        self.wait(0.2)
        self.sound_linked(key, row, pitches, glyphs, seconds)
        raised_notes = {}
        for form, index, label in (("harmonic", 6, forms[1]), ("melodic", 5, forms[2])):
            new_pitches = scale_of(key, form)
            new_row = place(self.scale_row(new_pitches), 0.0, SCALE_Y)
            new_note = new_row.notes[index].set_color(GREEN)
            new_tag = words(label, 36, GREEN, weight="BOLD").move_to(tag.get_right(), aligned_edge=RIGHT)
            self.play(ReplacementTransform(row.notes[index], new_note), FadeOut(tag), FadeIn(new_tag), run_time=0.45)
            self.shown[self.shown.index(row.notes[index])] = new_note
            self.shown[self.shown.index(tag)] = new_tag
            tag = new_tag
            row.notes[index] = new_note
            raised_notes[index] = GREEN
            pitches = new_pitches
            self.wait(0.15)
            self.sound_linked(key, row, pitches, glyphs, seconds, keep=raised_notes)
        self.wait(0.6)


class SharpMajors(KeyTour):
    def construct(self):
        # {[1]} Checkpoint: title; the two staves; C major with nothing to write
        self.title()
        keys = ["C", "G", "D", "A", "E", "B", "F#", "C#"]
        names, counts = split_list(self.t("keys")), split_list(self.t("counts"))
        self.stage()
        first = self.show_major("C", names[0], counts[0])
        self.caption("two-ways")
        self.caption("c-major", wait=False)
        self.play_major(first, hold=1.4)

        # {[2]} Checkpoint: G to B — one more sharp each time, lit in both places
        self.caption("one-more", wait=False)
        for i in range(1, 4):
            self.major_key(keys[i], names[i], counts[i])
        self.caption("twins", wait=False)
        for i in range(4, 6):
            self.major_key(keys[i], names[i], counts[i])

        # {[3]} Checkpoint: F sharp and C sharp major — six and seven sharps
        self.caption("last", wait=False)
        for i in range(6, 8):
            self.major_key(keys[i], names[i], counts[i], hold=1.4)
        self.caption("written-once", extra=0.5)

        # {[4]} Checkpoint: remember
        self.remember()


class FlatMajors(KeyTour):
    def construct(self):
        # {[1]} Checkpoint: title; the two staves; F major, one flat
        self.title()
        keys = ["F", "B-", "E-", "A-", "D-", "G-", "C-"]
        names, counts = split_list(self.t("keys")), split_list(self.t("counts"))
        self.stage()
        first = self.show_major("F", names[0], counts[0])
        self.caption("two-ways")
        self.caption("f-major", wait=False)
        self.play_major(first, hold=1.4)

        # {[2]} Checkpoint: B flat to D flat — one more flat each time
        self.caption("one-more", wait=False)
        for i in range(1, 3):
            self.major_key(keys[i], names[i], counts[i])
        self.caption("twins", wait=False)
        for i in range(3, 5):
            self.major_key(keys[i], names[i], counts[i])

        # {[3]} Checkpoint: G flat and C flat major — six and seven flats
        self.caption("last", wait=False)
        for i in range(5, 7):
            self.major_key(keys[i], names[i], counts[i], hold=1.4)
        self.caption("written-once", extra=0.5)

        # {[4]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 5. Enharmonic scales: F sharp major and G flat major


class EnharmonicScales(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; F sharp major on the staff and the keys
        self.title()
        sharp = scale_of("F#")
        row = row_of(sharp, y=1.1, staff_space=0.36, spacing=4.0)
        name = words(self.t("name-sharp"), 40, INK, weight="BOLD")
        name.next_to(row.staff, DOWN, buff=0.35).set_x(0)
        keyboard = Keyboard("E4", "G5", white_width=0.78, height=1.1)
        keyboard.move_to(np.array([0.0, -1.6, 0.0]))
        self.play(FadeIn(row), FadeIn(name), FadeIn(keyboard), run_time=0.6)
        self.caption("sharp", wait=False)
        sound_row(self, row, sharp, keyboard=keyboard)
        for pitch in sharp:
            keyboard.press(pitch, BLUE)
        self.wait(1.5)

        # {[2]} Checkpoint: respelled as G flat major — the same keys
        flat = scale_of("G-")
        flat_row = row_of(flat, y=1.1, staff_space=0.36, spacing=4.0)
        flat_name = words(self.t("name-flat"), 40, INK, weight="BOLD").move_to(name)
        self.caption("flat", wait=False)
        self.play(
            ReplacementTransform(VGroup(*row.notes), VGroup(*flat_row.notes)),
            Transform(name, flat_name),
            run_time=1.0,
        )
        self.wait(1.0)
        for pitch in sharp:
            keyboard.release(pitch)
        sound_row(self, flat_row, flat, keyboard=keyboard)
        for pitch in flat:
            keyboard.press(pitch, BLUE)
        self.wait(1.0)
        self.caption("same", extra=0.5)

        # {[3]} Checkpoint: the three enharmonic pairs
        self.clear_stage()
        pairs = VGroup(*(words(pair, 46, INK, weight="BOLD") for pair in split_list(self.t("pairs"))))
        pairs.arrange(DOWN, buff=0.45).move_to(np.array([0.0, 0.4, 0.0]))
        self.caption("pairs-caption", wait=False)
        self.play(FadeIn(pairs, lag_ratio=0.3), run_time=1.0)
        self.wait(3.0)

        # {[4]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 6. Minor: the smaller third


def half_step_count(keyboard: Keyboard, low: str, high: str, color=HIGHLIGHT) -> VGroup:
    """Numbers 1, 2, 3 ... just above the keyboard, one over every key
    above `low` up to `high`: the half steps, counted key by key."""
    from theoria.core.pitches import semitones_between

    group = VGroup()
    base = 60 + semitones_between("C4", low)
    top = keyboard.get_top()[1]
    for k in range(1, semitones_between(low, high) + 1):
        rect = keyboard.keys[base + k]
        number = words(str(k), 34, color, weight="BOLD")
        number.move_to(np.array([rect.get_center()[0], top + 0.3, 0.0]))
        group.add(number)
    return group


class TheSmallerThird(LessonScene):
    def third(self, keyboard, upper: str, color, labels, index: int, row):
        """Show one third: its column, its keys, its half steps counted."""
        self.play(FadeIn(row.notes[index]), FadeIn(labels[index // 2]), run_time=0.4)
        row.notes[index].set_color(color)
        keyboard.press("A4", color), keyboard.press(upper, color)
        numbers = half_step_count(keyboard, "A4", upper, color)
        add_pitches_sound(self, ["A4", upper], duration=1.4)
        self.wait(1.2)
        for number in numbers:
            self.play(FadeIn(number, shift=DOWN * 0.1), run_time=0.25)
            self.wait(0.3)
        add_sequence_sound(self, ["A4", upper], note_duration=1.0, qpm=90)
        self.wait(2.0)
        keyboard.release("A4"), keyboard.release(upper)
        row.notes[index].set_color(INK)
        return numbers

    def construct(self):
        # {[1]} Checkpoint: title; one interval names both modes
        self.title()
        row = row_of([["A4", "C#5"], None, ["A4", "C5"]], y=1.4, staff_space=0.4, spacing=4.0)
        labels = row.labels_under([self.t("label-major"), None, self.t("label-minor")], size=38)
        keyboard = Keyboard("A4", "E5", white_width=1.2, height=1.1)
        keyboard.move_to(np.array([0.0, -1.55, 0.0]))
        self.play(FadeIn(row.staff), FadeIn(row.clef), FadeIn(keyboard), run_time=0.5)
        self.caption("names", wait=False)
        self.wait(3.0)

        # {[2]} Checkpoint: A up to C sharp — four half steps
        self.caption("major-third", wait=False)
        numbers = self.third(keyboard, "C#5", HIGHLIGHT, labels, 0, row)
        self.play(FadeOut(numbers), run_time=0.3)

        # {[3]} Checkpoint: A up to C — three half steps, the smaller third
        self.caption("minor-third", wait=False)
        self.third(keyboard, "C5", BLUE, labels, 2, row)
        self.clear_stage()

        # {[4]} Checkpoint: the primitive minor scale on A
        pitches = scale_of("a")
        scale = row_of(pitches, y=0.6)
        keyboard = Keyboard("A4", "A5", white_width=0.85, height=1.1)
        keyboard.move_to(np.array([0.0, -1.6, 0.0]))
        self.play(FadeIn(scale), FadeIn(keyboard), run_time=0.5)
        self.caption("primitive", wait=False)
        sound_row(self, scale, pitches, keyboard=keyboard)
        marks = step_marks(scale, pitches)
        self.play(FadeIn(marks, lag_ratio=0.15), run_time=1.0)
        self.wait(2.5)

        # {[5]} Checkpoint: C major's tones, C major's signature: relative keys
        self.caption("relative", wait=False)
        sound_row(self, scale, pitches, keyboard=keyboard)
        for pitch in pitches:
            keyboard.press(pitch, BLUE)
        self.wait(3.0)

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 7. Three forms of A minor


class ThreeFormsOfAMinor(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; the primitive form, as the signature says
        self.title()
        pitches = scale_of("a")
        row = row_of(pitches, y=0.35, staff_space=0.42, duration="quarter")
        marks = step_marks(row, pitches)
        tag = words(self.t("tag-primitive"), 44, BLUE, weight="BOLD")
        tag.move_to(np.array([0.0, row.staff.get_bottom()[1] - 1.0, 0.0]))
        self.play(FadeIn(row), FadeIn(tag), run_time=0.5)
        self.caption("primitive", wait=False)
        sound_row(self, row, pitches)
        self.play(FadeIn(marks), run_time=0.5)
        self.wait(1.5)
        self.caption("no-leading", wait=False)
        self.play(marks[6].animate.set_color(RED).scale(1.3), run_time=0.4)
        add_sequence_sound(self, pitches[6:], note_duration=1.0, qpm=80)
        self.wait(3.0)

        # {[2]} Checkpoint: harmonic form — the seventh raised to G sharp
        harmonic = scale_of("a", "harmonic")
        h_row = row_of(harmonic, y=0.35, staff_space=0.42, duration="quarter")
        h_marks = step_marks(h_row, harmonic)
        h_row.notes[6].set_color(GREEN)
        self.caption("harmonic", wait=False)
        self.play(
            ReplacementTransform(row.notes[6], h_row.notes[6]),
            Transform(marks, h_marks),
            Transform(tag, words(self.t("tag-harmonic"), 44, BLUE, weight="BOLD").move_to(tag)),
            run_time=0.8,
        )
        row.notes[6] = h_row.notes[6]
        add_sequence_sound(self, harmonic[6:], note_duration=1.0, qpm=80)
        self.wait(2.6)
        self.caption("gap", wait=False)
        for _ in range(2):
            add_sequence_sound(self, harmonic[5:7], note_duration=1.0, qpm=70)
            self.wait(1.9)
        sound_row(self, row, harmonic, after=lambda i: GREEN if i == 6 else INK)
        self.wait(1.0)

        # {[3]} Checkpoint: melodic form going up — six and seven raised
        melodic = scale_of("a", "melodic")
        m_row = row_of(melodic, y=0.35, staff_space=0.42, duration="quarter")
        m_marks = step_marks(m_row, melodic)
        m_row.notes[5].set_color(GREEN)
        self.caption("melodic", wait=False)
        self.play(
            ReplacementTransform(row.notes[5], m_row.notes[5]),
            Transform(marks, m_marks),
            Transform(tag, words(self.t("tag-melodic-up"), 44, BLUE, weight="BOLD").move_to(tag)),
            run_time=0.8,
        )
        row.notes[5] = m_row.notes[5]
        sound_row(self, row, melodic, after=lambda i: GREEN if i in (5, 6) else INK)
        self.wait(2.0)

        # {[4]} Checkpoint: melodic coming down — back to the primitive form
        down_row = row_of(pitches, y=0.35, staff_space=0.42, duration="quarter")
        self.caption("down", wait=False)
        self.play(
            ReplacementTransform(row.notes[5], down_row.notes[5]),
            ReplacementTransform(row.notes[6], down_row.notes[6]),
            Transform(marks, step_marks(down_row, pitches)),
            Transform(tag, words(self.t("tag-melodic-down"), 44, BLUE, weight="BOLD").move_to(tag)),
            run_time=0.8,
        )
        row.notes[5], row.notes[6] = down_row.notes[5], down_row.notes[6]
        sound_row(self, row, pitches, order=range(7, -1, -1))
        self.wait(1.5)

        # {[5]} Checkpoint: the lower tetrachord never changes
        self.caption("lower-same", wait=False)
        low = min(row.notes[i].get_bottom()[1] for i in range(4)) - 0.25
        lower = bracket(row.note_x(0) - 0.4, row.note_x(3) + 0.4, low, self.t("lower-label"), color=HIGHLIGHT, size=38)
        self.play(FadeOut(marks), FadeOut(tag), run_time=0.3)
        self.play(FadeIn(lower), *(row.notes[i].animate.set_color(HIGHLIGHT) for i in range(4)), run_time=0.5)
        add_sequence_sound(self, pitches[:4], note_duration=1.0, qpm=120)
        self.wait(3.5)

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 8-9. The minor keys, three forms each


class SharpMinors(KeyTour):
    def construct(self):
        # {[1]} Checkpoint: title; the two staves; A minor in three forms
        self.title()
        keys = ["a", "e", "b", "f#", "c#", "g#", "d#", "a#"]
        names, counts = split_list(self.t("keys")), split_list(self.t("counts"))
        forms = split_list(self.t("forms"))
        self.stage()
        self.caption("two-ways", wait=False)
        self.minor_key("a", names[0], counts[0], forms)

        # {[2]} Checkpoint: E to C sharp minor — raised notes are accidentals
        self.caption("raised", wait=False)
        for i in range(1, 3):
            self.minor_key(keys[i], names[i], counts[i], forms)
        self.caption("signature", wait=False)
        for i in range(3, 5):
            self.minor_key(keys[i], names[i], counts[i], forms)

        # {[3]} Checkpoint: G sharp, D sharp, A sharp minor — double sharps
        self.caption("double", wait=False)
        for i in range(5, 8):
            self.minor_key(keys[i], names[i], counts[i], forms)

        # {[4]} Checkpoint: remember
        self.remember()


class FlatMinors(KeyTour):
    def construct(self):
        # {[1]} Checkpoint: title; the two staves; D minor in three forms
        self.title()
        keys = ["d", "g", "c", "f", "b-", "e-", "a-"]
        names, counts = split_list(self.t("keys")), split_list(self.t("counts"))
        forms = split_list(self.t("forms"))
        self.stage()
        self.caption("two-ways", wait=False)
        self.minor_key("d", names[0], counts[0], forms)

        # {[2]} Checkpoint: G to F minor — raising can mean cancelling a flat
        self.caption("cancel", wait=False)
        for i in range(1, 4):
            self.minor_key(keys[i], names[i], counts[i], forms)

        # {[3]} Checkpoint: B flat, E flat, A flat minor
        self.caption("signature", wait=False)
        for i in range(4, 7):
            self.minor_key(keys[i], names[i], counts[i], forms)

        # {[4]} Checkpoint: remember
        self.remember()

"""Module 07 lessons (Gehrkens ch. XVII): intervals — harmonic and
melodic, the number from the staff degrees, the quality from the half
steps, the major/perfect intervals above the tonic, the quality ladder,
and inversion.

One idea per video; every word on screen comes from content/<lang>/.

Render (from the repo root):
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/07-intervals/scenes.py CountingStaffDegrees -w -l
"""

import numpy as np
from manimlib import DOWN, RIGHT, UP, FadeIn, FadeOut, VGroup

from theoria.audio import add_pitches_sound, add_sequence_sound
from theoria.core.pitches import semitones_between
from theoria.notation.lesson import (
    Keyboard,
    LessonScene,
    NoteRow,
    words,
)
from theoria.theme import BLUE, GREEN, HIGHLIGHT, INK, MUTED, RED


def place(row: NoteRow, x: float, y: float) -> NoteRow:
    """Put a row's STAFF centre at (x, y), whatever the notes' range."""
    row.shift(np.array([x, y, 0.0]) - row.staff.get_center())
    return row


def row_of(entries, x: float = 0.0, y: float = 0.8, staff_space: float = 0.45, spacing: float = 4.0, **margins) -> NoteRow:
    row = NoteRow(entries, staff_space=staff_space, spacing_ss=spacing, duration="whole", **margins)
    return place(row, x, y)


def unison_apart(row: NoteRow, i: int):
    """A prime (two heads on one degree) drawn side by side, as engravers
    do — NoteRow would stack the two heads on top of each other."""
    parts = row.notes[i]
    second = VGroup(*parts[len(parts) // 2 :])
    second.shift(RIGHT * 1.75 * row.staff.staff_space)


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


def big(text: str, color=HIGHLIGHT, size: float = 54):
    return words(text, size, color, weight="BOLD")


def half_step_count(keyboard: Keyboard, low: str, high: str, color=HIGHLIGHT) -> VGroup:
    """Numbers 1, 2, 3 ... just above the keyboard, one over every key
    above `low` up to `high`: the half steps, counted key by key."""
    group = VGroup()
    base = 60 + semitones_between("C4", low)
    top = keyboard.get_top()[1]
    for k in range(1, semitones_between(low, high) + 1):
        rect = keyboard.keys[base + k]
        number = words(str(k), 34, color, weight="BOLD")
        number.move_to(np.array([rect.get_center()[0], top + 0.3, 0.0]))
        group.add(number)
    return group


def split_list(text: str) -> list[str]:
    return [part.strip() for part in text.split(",")]


# ---------------------------------------------------------------------------


class HarmonicOrMelodic(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; F and A, the book's own pair
        self.title()
        row = row_of([["F4", "A4"], None, "F4", "A4"], y=0.9, staff_space=0.5, spacing=4.2)
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.5)
        self.caption("interval", wait=False)
        self.play(FadeIn(row.notes[0]), run_time=0.4)
        add_pitches_sound(self, ["F4", "A4"], duration=1.5)
        self.wait(3.2)

        # {[2]} Checkpoint: together — a harmonic interval
        harmonic = row.label_under(0, self.t("label-harmonic"), size=40, color=BLUE)
        self.caption("harmonic", wait=False)
        self.play(FadeIn(harmonic), row.notes[0].animate.set_color(BLUE), run_time=0.4)
        for _ in range(2):
            add_pitches_sound(self, ["F4", "A4"], duration=1.3)
            self.wait(1.6)
        row.notes[0].set_color(INK)

        # {[3]} Checkpoint: one after the other — a melodic interval
        melodic = row.label_between(2, 3, self.t("label-melodic"), size=40, color=HIGHLIGHT, above=False)
        melodic.set_y(harmonic.get_y())
        self.caption("melodic", wait=False)
        self.play(FadeIn(row.notes[2]), FadeIn(row.notes[3]), FadeIn(melodic), run_time=0.4)
        for _ in range(2):
            add_sequence_sound(self, ["F4", "A4"], note_duration=1.0, qpm=80)
            for i in (2, 3):
                row.notes[i].set_color(HIGHLIGHT)
                self.wait(0.75)
                row.notes[i].set_color(INK)
            self.wait(0.3)

        # {[4]} Checkpoint: the same two tones, the same interval
        self.caption("same", wait=False)
        name = big(self.t("label-third"), INK, 50)
        name.next_to(row.staff, UP, buff=0.35)
        self.play(FadeIn(name), run_time=0.4)
        row.notes[0].set_color(BLUE)
        add_pitches_sound(self, ["F4", "A4"], duration=1.2)
        self.wait(1.4)
        row.notes[0].set_color(INK)
        add_sequence_sound(self, ["F4", "A4"], note_duration=1.0, qpm=80)
        for i in (2, 3):
            row.notes[i].set_color(HIGHLIGHT)
            self.wait(0.75)
            row.notes[i].set_color(INK)
        self.wait(2.0)

        # {[5]} Checkpoint: remember
        self.remember()


class CountingStaffDegrees(LessonScene):
    def counted(self, pitches: list[str], name: str, x: float = -1.4):
        """The two ends in ink, the degrees between as grey ghosts, all
        numbered; the interval's number name to the right."""
        row = row_of(pitches, x=x, y=0.8, staff_space=0.45, spacing=3.2)
        for i in range(1, len(pitches) - 1):
            row.notes[i].set_color(MUTED)
        numbers = row.labels_under([str(i + 1) for i in range(len(pitches))], color=MUTED, size=36)
        label = big(name).next_to(row, RIGHT, buff=0.5)
        return row, numbers, label

    def count(self, pitches: list[str], name: str, key: str):
        """Count each staff degree, both ends included, then name it."""
        row, numbers, label = self.counted(pitches, self.t(name))
        self.play(FadeIn(row), run_time=0.4)
        add_sequence_sound(self, [pitches[0], pitches[-1]], note_duration=1.0, qpm=80)
        self.caption(key, wait=False)
        self.wait(1.0)
        for number in numbers:
            self.play(number.animate.set_color(HIGHLIGHT), run_time=0.25)
            self.wait(0.3)
        self.play(FadeIn(label, scale=1.3), run_time=0.4)
        add_pitches_sound(self, [pitches[0], pitches[-1]], duration=1.4)
        self.wait(3.0)
        self.play(FadeOut(row), FadeOut(numbers), FadeOut(label), run_time=0.3)

    def construct(self):
        # {[1]} Checkpoint: title; C up to E counts three staff degrees
        self.title()
        self.count(["C4", "D4", "E4"], "label-third", "third")

        # {[2]} Checkpoint: C up to G counts five
        self.count(["C4", "D4", "E4", "F4", "G4"], "label-fifth", "fifth")

        # {[3]} Checkpoint: accidentals never change the number
        fifths = (["C4", "G4"], ["C4", "G#4"], ["C#4", "G-4"], ["C-4", "G#4"])
        row = row_of(list(fifths), y=0.9, staff_space=0.45, spacing=6.4)
        for i in range(len(fifths)):
            tidy_accidentals(row, i)
        labels = row.labels_under([self.t("label-fifth")] * 4, size=40, color=HIGHLIGHT)
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
        self.caption("accidentals", wait=False)
        for i, pitches in enumerate(fifths):
            self.play(FadeIn(row.notes[i]), FadeIn(labels[i]), run_time=0.35)
            add_pitches_sound(self, pitches, duration=1.1)
            self.wait(1.4)
        self.wait(1.5)

        # {[4]} Checkpoint: they sound different — that is the quality's job
        self.caption("sizes", wait=False)
        for i, pitches in enumerate(fifths):
            row.notes[i].set_color(BLUE)
            add_pitches_sound(self, pitches, duration=0.9)
            self.wait(1.0)
            row.notes[i].set_color(INK)
        self.wait(1.5)

        # {[5]} Checkpoint: remember
        self.remember()


class CountingHalfSteps(LessonScene):
    def show(self, row: NoteRow, labels, keyboard: Keyboard, i: int, low: str, high: str, key: str, color):
        """One interval: its column, its keys, its half steps counted."""
        self.caption(key, wait=False)
        self.play(FadeIn(row.notes[i]), FadeIn(labels[i]), run_time=0.4)
        row.notes[i].set_color(color)
        keyboard.press(low, color), keyboard.press(high, color)
        add_pitches_sound(self, [low, high], duration=1.3)
        self.wait(1.0)
        numbers = half_step_count(keyboard, low, high, color)
        for number in numbers:
            self.play(FadeIn(number, shift=DOWN * 0.1), run_time=0.25)
            self.wait(0.3)
        add_sequence_sound(self, [low, high], note_duration=1.0, qpm=90)
        self.wait(1.7)
        keyboard.release(low), keyboard.release(high)
        row.notes[i].set_color(INK)
        self.play(FadeOut(numbers), run_time=0.25)

    def group(self, intervals, low_key: str, high_key: str, keys: list[str], label_keys: list[str], colors, intro: str | None = None):
        row = row_of([list(p) for p in intervals], y=1.45, staff_space=0.38, spacing=7.4)
        labels = row.labels_under([self.t(k) for k in label_keys], size=36)
        keyboard = Keyboard(low_key, high_key, white_width=1.0, height=1.1)
        keyboard.move_to(np.array([0.0, -1.75, 0.0]))
        self.play(FadeIn(row.staff), FadeIn(row.clef), FadeIn(keyboard), run_time=0.5)
        if intro:
            self.caption(intro)
        for i, ((low, high), key, color) in enumerate(zip(intervals, keys, colors)):
            self.show(row, labels, keyboard, i, low, high, key, color)
        return row, labels, keyboard

    def construct(self):
        # {[1]} Checkpoint: title
        self.title()

        # {[2]} Checkpoint: the half step is the unit; three seconds — 1, 2 and 3 half steps
        self.group(
            (("B4", "C5"), ("B4", "C#5"), ("F4", "G#4")),
            "F4", "D5",
            ["minor-second", "major-second", "augmented-second"],
            ["label-m2", "label-M2", "label-A2"],
            (BLUE, HIGHLIGHT, GREEN),
            intro="unit",
        )
        self.caption("seconds", extra=0.5)
        self.clear_stage()

        # {[3]} Checkpoint: three thirds — 2, 3 and 4 half steps
        self.group(
            (("C4", "E--4"), ("C4", "E-4"), ("C4", "E4")),
            "C4", "A4",
            ["diminished-third", "minor-third", "major-third"],
            ["label-d3", "label-m3", "label-M3"],
            (RED, BLUE, HIGHLIGHT),
        )
        self.caption("thirds", extra=0.5)

        # {[4]} Checkpoint: remember
        self.remember()


_FROM_C = ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5")
_MAJOR = (1, 2, 5, 6)  # 2nd, 3rd, 6th, 7th
_PERFECT = (0, 3, 4, 7)  # prime, 4th, 5th, octave


class AboveTheTonic(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; every tone of C major measured from C
        self.title()
        row = row_of(
            [["C4", upper] for upper in _FROM_C], y=0.7, staff_space=0.36, spacing=4.3,
            left_margin_ss=5.0, right_margin_ss=1.0,
        )
        unison_apart(row, 0)
        names = row.labels_under(split_list(self.t("names")), size=40)
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
        self.caption("measure", wait=False)
        for i, upper in enumerate(_FROM_C):
            self.play(FadeIn(row.notes[i]), FadeIn(names[i]), run_time=0.3)
            add_pitches_sound(self, ["C4", upper], duration=0.9)
            self.wait(0.8)
        self.wait(1.2)

        # {[2]} Checkpoint: 2nd, 3rd, 6th, 7th are major
        self.caption("major", wait=False)
        self.play(
            *(row.notes[i].animate.set_color(BLUE) for i in _MAJOR),
            *(names[i].animate.set_color(BLUE).scale(1.12) for i in _MAJOR),
            run_time=0.5,
        )
        for i in _MAJOR:
            add_pitches_sound(self, ["C4", _FROM_C[i]], duration=0.8)
            self.wait(0.8)
        self.wait(1.5)

        # {[3]} Checkpoint: prime, 4th, 5th, octave are perfect
        self.caption("perfect", wait=False)
        self.play(
            *(row.notes[i].animate.set_color(HIGHLIGHT) for i in _PERFECT),
            *(names[i].animate.set_color(HIGHLIGHT).scale(1.12) for i in _PERFECT),
            run_time=0.5,
        )
        for i in _PERFECT:
            add_pitches_sound(self, ["C4", _FROM_C[i]], duration=0.8)
            self.wait(0.8)
        self.wait(1.5)

        # {[4]} Checkpoint: no minor, no diminished above the tonic
        self.caption("none-smaller", extra=0.5)

        # {[5]} Checkpoint: remember
        self.remember()


class TheQualityLadder(LessonScene):
    def ladder(self, intervals, name_keys, colors, counts_word: str, y: float = 0.95):
        row = row_of([list(p) for p in intervals], y=y, staff_space=0.45, spacing=6.2)
        names = row.labels_under([self.t(k) for k in name_keys], size=38)
        counts = VGroup()
        for i, (low, high) in enumerate(intervals):
            count = words(f"{semitones_between(low, high)} {counts_word}", 30, MUTED)
            count.next_to(names[i], DOWN, buff=0.18).set_x(names[i].get_x())
            counts.add(count)
        return row, names, counts

    def climb(self, row, names, counts, intervals, colors):
        for i, ((low, high), color) in enumerate(zip(intervals, colors)):
            self.play(FadeIn(row.notes[i]), FadeIn(names[i]), FadeIn(counts[i]), run_time=0.35)
            row.notes[i].set_color(color), names[i].set_color(color)
            add_pitches_sound(self, [low, high], duration=1.1)
            self.wait(1.5)

    def construct(self):
        # {[1]} Checkpoint: title; four thirds, a half step apart
        self.title()
        word = self.t("half-steps")
        thirds = (("C4", "E--4"), ("C4", "E-4"), ("C4", "E4"), ("C4", "E#4"))
        third_colors = (RED, BLUE, HIGHLIGHT, GREEN)
        row, names, counts = self.ladder(thirds, ["dim", "minor", "major", "aug"], third_colors, word)
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
        self.caption("thirds", wait=False)
        self.climb(row, names, counts, thirds, third_colors)
        self.wait(1.0)

        # {[2]} Checkpoint: smaller than major: minor, then diminished
        self.caption("down-major", wait=False)
        for i in (2, 1, 0):
            row.notes[i].set_color(INK)
            add_pitches_sound(self, list(thirds[i]), duration=0.9)
            row.notes[i].set_color(third_colors[i])
            self.play(names[i].animate.scale(1.15), run_time=0.3)
            self.wait(0.9)
            self.play(names[i].animate.scale(1 / 1.15), run_time=0.2)
        self.caption("up-major", wait=False)
        self.play(names[3].animate.scale(1.15), run_time=0.3)
        add_pitches_sound(self, list(thirds[3]), duration=1.0)
        self.wait(2.6)
        self.clear_stage()

        # {[3]} Checkpoint: perfect has no minor: diminished, perfect, augmented
        fifths = (("C4", "G-4"), ("C4", "G4"), ("C4", "G#4"))
        fifth_colors = (RED, HIGHLIGHT, GREEN)
        row, names, counts = self.ladder(fifths, ["dim", "perfect", "aug"], fifth_colors, word)
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
        self.caption("fifths", wait=False)
        self.climb(row, names, counts, fifths, fifth_colors)
        self.wait(1.0)
        self.caption("perfect-rule", extra=0.5)

        # {[4]} Checkpoint: remember
        self.remember()


class InvertingIntervals(LessonScene):
    def flip(self, lower: str, upper: str, octave_up: str, before: str, after: str, key: str):
        """The interval at left; its lower tone travels up an octave and
        the inversion appears at right."""
        left = row_of([[lower, upper]], x=-3.2, y=0.9, staff_space=0.5, spacing=3.0)
        right = row_of([[upper, octave_up]], x=3.2, y=0.9, staff_space=0.5, spacing=3.0)
        label_left = big(before, INK, 44).next_to(VGroup(left.staff, left.notes[0]), DOWN, buff=0.4)
        label_right = big(after, BLUE, 44).next_to(right.staff, DOWN, buff=0.4).set_y(label_left.get_y())
        self.play(FadeIn(left), FadeIn(label_left), run_time=0.5)
        add_pitches_sound(self, [lower, upper], duration=1.3)
        self.wait(1.6)
        self.caption("move", wait=False)
        self.play(FadeIn(right.staff), FadeIn(right.clef), run_time=0.4)
        heads = list(right.notes[0])  # lower head, its ledgers, upper head, ...
        # the moving tone: a copy of the lower note flies up to its octave
        mover = left.notes[0][0].copy().set_color(HIGHLIGHT)
        self.play(FadeIn(VGroup(*heads[:2])), run_time=0.3)
        self.play(mover.animate.move_to(heads[2].get_center()), run_time=1.0)
        self.remove(mover)
        right.notes[0][2].set_color(HIGHLIGHT)
        self.add(right.notes[0])
        add_pitches_sound(self, [upper, octave_up], duration=1.3)
        self.caption(key, wait=False)
        self.play(FadeIn(label_right), run_time=0.4)
        self.wait(2.6)
        return VGroup(left, right, label_left, label_right)

    def construct(self):
        # {[1]} Checkpoint: title; C-E, a major third, turned over
        self.title()
        group = self.flip("C4", "E4", "C5", self.t("name-M3"), self.t("name-m6"), "third")

        # {[2]} Checkpoint: the numbers add up to nine
        nine = big("3 + 6 = 9", HIGHLIGHT, 60).move_to(np.array([0.0, -1.95, 0.0]))
        self.play(FadeIn(nine, scale=1.2), run_time=0.4)
        self.caption("nine", extra=0.5)
        self.play(FadeOut(group), FadeOut(nine), run_time=0.4)

        # {[3]} Checkpoint: C-G, a perfect fifth, turned over
        group = self.flip("C4", "G4", "C5", self.t("name-P5"), self.t("name-P4"), "fifth")
        nine = big("5 + 4 = 9", HIGHLIGHT, 60).move_to(np.array([0.0, -1.95, 0.0]))
        self.play(FadeIn(nine, scale=1.2), run_time=0.4)
        self.wait(2.2)
        self.play(FadeOut(group), FadeOut(nine), run_time=0.4)

        # {[4]} Checkpoint: how the qualities trade places
        swaps = VGroup(
            words(self.t("swap-major"), 46, BLUE),
            words(self.t("swap-aug"), 46, RED),
            words(self.t("swap-perfect"), 46, HIGHLIGHT),
        ).arrange(DOWN, buff=0.55).move_to(np.array([0.0, 0.5, 0.0]))
        self.play(FadeIn(swaps, lag_ratio=0.3), run_time=0.8)
        self.caption("qualities", extra=1.0)

        # {[5]} Checkpoint: remember
        self.remember()

"""Module 01 lessons (Gehrkens chs. I-III): seeing music — the staff and
its degrees, clefs, the great staff and middle C, the parts of a note,
and which way stems point.

One idea per video; every word on screen comes from content/<lang>/.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/01-seeing-music/scenes.py TheStaff -w -l
"""

import re

import numpy as np
from manimlib import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    FadeIn,
    FadeOut,
    GrowFromEdge,
    Rectangle,
    ShowCreation,
    VGroup,
    linear,
)

from theoria.audio import add_pitches_sound, add_sequence_sound
from theoria.core.examples import example_events, snippet
from theoria.notation.glyphs import NamedNotehead, Notehead, SmuflGlyph, stem_for
from theoria.notation.lesson import (
    LABEL_SIZE,
    SMALL_SIZE,
    LessonScene,
    NoteRow,
    engraved,
    lit_play,
    play_row,
    reading_time,
    words,
    wrap,
)
from theoria.notation.staff import STAFF_REFERENCE, Staff, grand_staff_for
from theoria.core.pitches import diatonic_steps_from
from theoria.theme import BLUE, HIGHLIGHT, INK, MUTED


def _band(staff: Staff, step: float, color=BLUE, opacity: float = 0.18) -> Rectangle:
    """A tinted strip over one staff degree (a space, or the band of a line)."""
    ss = staff.staff_space
    band = Rectangle(
        width=staff.width_ss * ss, height=ss * 0.6,
        fill_color=color, fill_opacity=opacity, stroke_width=0,
    )
    band.move_to(staff.point_for(staff.width_ss / 2, step))
    return band


def _line_glow(staff: Staff, index: int, color=HIGHLIGHT) -> Rectangle:
    """A thick coloured copy of staff line `index` (0 = bottom line)."""
    line = staff.lines[index]
    return Rectangle(
        width=line.get_width(), height=staff.staff_space * 0.16,
        fill_color=color, fill_opacity=1.0, stroke_width=0,
    ).move_to(line.get_center())


def _head(staff: Staff, pitch: str, x_ss: float, clef: str = "treble", named: bool = False,
          duration: str = "whole", color=INK) -> VGroup:
    """One notehead (letter inside if `named`) plus any ledger lines."""
    step = diatonic_steps_from(pitch, STAFF_REFERENCE[clef])
    if named:
        head = NamedNotehead(pitch[0], duration, staff_space=staff.staff_space, color=color)
    else:
        head = Notehead(duration, staff_space=staff.staff_space, color=color)
    staff.place(head, x_ss, step)
    width = 1.7 if duration == "whole" else 1.2
    return VGroup(head, staff.ledger_lines(x_ss, step, head_width_ss=width * 0.75))


def _rebeam(xml: str, groups: list[tuple[int, str]]) -> str:
    """Re-group the beams of a snippet's eighth notes: `groups` is a list of
    (notes in the group, stem direction). music21 beams 4/4 eighths in
    pairs; groups of four make the stem-direction rule visible."""
    notes = list(re.finditer(r"<note>.*?</note>", xml, re.S))
    plan = []
    for size, direction in groups:
        for i in range(size):
            kind = "begin" if i == 0 else ("end" if i == size - 1 else "continue")
            plan.append((kind, direction))
    out, last = [], 0
    for match, (kind, direction) in zip(notes, plan):
        note = match.group(0)
        note = re.sub(r"\s*<stem>\w+</stem>", "", note)
        note = re.sub(r"\s*<beam[^>]*>\w+</beam>", "", note)
        note = note.replace("</type>", f"</type><stem>{direction}</stem><beam number=\"1\">{kind}</beam>", 1)
        out += [xml[last:match.start()], note]
        last = match.end()
    out.append(xml[last:])
    return "".join(out)


class TheStaff(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title
        self.title()
        ss = 0.5
        staff = Staff(width_ss=20.0, staff_space=ss)
        staff.move_to(np.array([-0.3, 0.35, 0.0]))

        # {[2]} Checkpoint: five lines, counted from the bottom up
        numbers = VGroup(
            *(words(str(i + 1), LABEL_SIZE).next_to(line, LEFT, buff=0.35) for i, line in enumerate(staff.lines))
        )
        self.caption("lines", wait=False)
        for line, number in zip(staff.lines, numbers):
            self.play(ShowCreation(line), FadeIn(number), run_time=0.5)
        self.add(staff)
        self.wait(2.2)

        # {[3]} Checkpoint: four spaces between, one below, one above
        self.caption("spaces", wait=False)
        inner = VGroup(*(_band(staff, step) for step in (1, 3, 5, 7)))
        inner_numbers = VGroup(
            *(
                words(str(i + 1), LABEL_SIZE, BLUE).next_to(band, RIGHT, buff=0.3)
                for i, band in enumerate(inner)
            )
        )
        for band, number in zip(inner, inner_numbers):
            self.play(FadeIn(band), FadeIn(number), run_time=0.4)
        outer = VGroup(_band(staff, -1, MUTED, 0.22), _band(staff, 9, MUTED, 0.22))
        outer_labels = VGroup(
            words(self.t("label-below"), LABEL_SIZE, MUTED).next_to(outer[0], RIGHT, buff=0.3),
            words(self.t("label-above"), LABEL_SIZE, MUTED).next_to(outer[1], RIGHT, buff=0.3),
        )
        self.play(FadeIn(outer), FadeIn(outer_labels), run_time=0.6)
        self.wait(3.5)
        self.play(FadeOut(inner), FadeOut(outer), FadeOut(inner_numbers), FadeOut(outer_labels), FadeOut(numbers), run_time=0.5)

        # {[4]} Checkpoint: one note on every degree, bottom to top, played
        pitches = ["D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5"]
        heads = VGroup(*(_head(staff, p, 2.2 + 1.65 * i, duration="quarter") for i, p in enumerate(pitches)))
        self.caption("degree", wait=False)
        for head, pitch in zip(heads, pitches):
            add_pitches_sound(self, [pitch], duration=0.55)
            self.play(FadeIn(head, scale=1.3), run_time=0.2)
            self.wait(0.3)
        self.wait(2.0)

        # {[5]} Checkpoint: the climb again — the sound rises with the notes
        self.caption("climb", wait=False)
        add_sequence_sound(self, pitches, note_duration=1.0, qpm=60 / 0.4)
        for head in heads:
            head.set_color(HIGHLIGHT)
            self.wait(0.4)
            head.set_color(INK)
        self.wait(1.8)
        self.play(FadeOut(heads), run_time=0.4)

        # {[6]} Checkpoint: low note, high note: higher on the staff, higher in pitch
        low = _head(staff, "E4", 5.0)
        high = _head(staff, "F5", 14.0)
        self.play(FadeIn(low), FadeIn(high), run_time=0.4)
        self.caption("higher", wait=False)
        for _ in range(2):
            for mob, pitch in ((low, "E4"), (high, "F5")):
                mob.set_color(HIGHLIGHT)
                add_pitches_sound(self, [pitch], duration=0.8)
                self.wait(0.9)
                mob.set_color(INK)
        self.wait(1.2)

        # {[7]} Checkpoint: remember
        self.remember()


class TheClefs(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a treble staff with its clef
        self.title()
        treble = ["E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5"]
        row = NoteRow(treble, named=True, duration="whole", staff_space=0.44, spacing_ss=2.5)
        row.move_to(np.array([0.0, 0.45, 0.0]))
        self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.5)

        # {[2]} Checkpoint: the G clef curls around the second line: G
        glow = _line_glow(row.staff, 1)
        self.caption("gclef", wait=False)
        self.play(row.clef.animate.set_color(HIGHLIGHT), FadeIn(glow), run_time=0.5)
        self.play(FadeIn(row.notes[2], scale=1.3), run_time=0.3)
        add_pitches_sound(self, ["G4"], duration=1.2)
        self.wait(4.2)

        # {[3]} Checkpoint: the letters run up and down from G
        self.caption("gnames", wait=False)
        self.play(row.clef.animate.set_color(INK), FadeOut(glow), run_time=0.3)
        for i in (3, 4, 5, 6, 7, 8, 1, 0):
            add_pitches_sound(self, [treble[i]], duration=0.6)
            self.play(FadeIn(row.notes[i], scale=1.3), run_time=0.2)
            self.wait(0.35)
        play_row(self, row, treble, seconds=0.4)
        self.wait(1.0)
        self.play(FadeOut(row), run_time=0.4)

        # {[4]} Checkpoint: the F clef's dots around the fourth line: F
        bass = ["G2", "A2", "B2", "C3", "D3", "E3", "F3", "G3", "A3"]
        brow = NoteRow(bass, clef="bass", named=True, duration="whole", staff_space=0.44, spacing_ss=2.5)
        brow.move_to(np.array([0.0, 0.45, 0.0]))
        self.play(FadeIn(brow.staff), FadeIn(brow.clef), run_time=0.5)
        glow = _line_glow(brow.staff, 3)
        self.caption("fclef", wait=False)
        self.play(brow.clef.animate.set_color(HIGHLIGHT), FadeIn(glow), run_time=0.5)
        self.play(FadeIn(brow.notes[6], scale=1.3), run_time=0.3)
        add_pitches_sound(self, ["F3"], duration=1.2)
        self.wait(4.5)

        # {[5]} Checkpoint: the same alphabet, counted from F
        self.caption("fnames", wait=False)
        self.play(brow.clef.animate.set_color(INK), FadeOut(glow), run_time=0.3)
        for i in (7, 8, 5, 4, 3, 2, 1, 0):
            add_pitches_sound(self, [bass[i]], duration=0.6)
            self.play(FadeIn(brow.notes[i], scale=1.3), run_time=0.2)
            self.wait(0.35)
        play_row(self, brow, bass, seconds=0.4)
        self.wait(0.6)
        self.play(FadeOut(brow), run_time=0.4)

        # {[6]} Checkpoint: same line, two clefs, two notes
        left = NoteRow(["G4"], named=True, duration="whole", staff_space=0.5, left_margin_ss=6.0, right_margin_ss=2.5)
        right = NoteRow(["B2"], clef="bass", named=True, duration="whole", staff_space=0.5, left_margin_ss=6.0, right_margin_ss=2.5)
        left.move_to(np.array([-3.2, 0.45, 0.0]))
        right.move_to(np.array([3.2, 0.45, 0.0]))
        glows = VGroup(_line_glow(left.staff, 1, BLUE), _line_glow(right.staff, 1, BLUE))
        self.play(FadeIn(left), FadeIn(right), FadeIn(glows), run_time=0.5)
        self.add(left.notes[0], right.notes[0])  # heads above the glow
        self.caption("same", wait=False)
        for _ in range(2):
            for row_, pitch in ((left, "G4"), (right, "B2")):
                row_.notes[0].set_color(HIGHLIGHT)
                add_pitches_sound(self, [pitch], duration=1.0)
                self.wait(1.1)
                row_.notes[0].set_color(INK)
        self.wait(0.8)
        self.play(FadeOut(VGroup(left, right, glows)), run_time=0.4)

        # {[7]} Checkpoint: the C clef centres on middle C
        staff = Staff(width_ss=11.0, staff_space=0.5)
        staff.move_to(np.array([0.0, 0.45, 0.0]))
        cclef = staff.place(SmuflGlyph("cClef", staff_space=0.5), 0.8, 4)
        middle_c = NamedNotehead("C", "whole", staff_space=0.5)
        staff.place(middle_c, 6.5, 4)
        self.play(FadeIn(staff), FadeIn(cclef), run_time=0.5)
        glow = _line_glow(staff, 2)
        self.caption("cclef", wait=False)
        self.play(cclef.animate.set_color(HIGHLIGHT), FadeIn(glow), run_time=0.4)
        self.play(FadeIn(middle_c, scale=1.3), run_time=0.3)
        add_pitches_sound(self, ["C4"], duration=1.5)
        self.wait(3.5)

        # {[8]} Checkpoint: remember
        self.remember()


class TheGreatStaff(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; treble and bass staves, brace and clefs
        self.title()
        walk = ["F3", "G3", "A3", "B3", "C4", "D4", "E4", "F4", "G4"]
        usable = 12.6
        _, xs = grand_staff_for(len(walk), base_staff_space=0.45, usable_width=usable)
        ss = 0.45 * 0.8  # grand_staff_for's size for nine slots
        width_ss = usable / ss
        treble = Staff(width_ss=width_ss, staff_space=ss)
        bass = Staff(width_ss=width_ss, staff_space=ss)
        # one ledger line apart: E4 line - (C4 ledger) - A3 line, 2 ss gap
        treble.move_to(np.array([0.2, 1.05, 0.0]))
        bass.move_to(treble.get_center() + DOWN * 6 * ss)
        t_clef = treble.clef("gClef", x_ss=1.0)
        b_clef = bass.clef("fClef", x_ss=1.0)
        left_bar = Rectangle(
            width=0.03, height=treble.get_top()[1] - bass.get_bottom()[1],
            fill_color=INK, fill_opacity=1, stroke_width=0,
        ).move_to(np.array([treble.get_left()[0], (treble.get_top()[1] + bass.get_bottom()[1]) / 2, 0]))
        brace = SmuflGlyph("brace", staff_space=ss)
        brace.stretch_to_fit_height(left_bar.get_height()).next_to(left_bar, LEFT, buff=0.08)
        top_group = VGroup(treble, t_clef)
        low_group = VGroup(bass, b_clef)
        self.caption("two", wait=False)
        self.play(FadeIn(top_group, shift=DOWN * 0.2), FadeIn(low_group, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(left_bar), FadeIn(brace), run_time=0.4)
        self.wait(2.6)

        # {[2]} Checkpoint: one short line between them: middle C
        mid_x = width_ss / 2
        c_treble = _head(treble, "C4", mid_x, named=True)
        c_label = words(self.t("label-middle-c"), LABEL_SIZE, HIGHLIGHT)
        c_label.next_to(c_treble, RIGHT, buff=0.5)
        self.caption("middle", wait=False)
        self.play(ShowCreation(c_treble[1]), run_time=0.5)
        self.play(FadeIn(c_treble[0], scale=1.3), FadeIn(c_label), run_time=0.4)
        c_treble.set_color(HIGHLIGHT)
        add_pitches_sound(self, ["C4"], duration=1.5)
        self.wait(3.2)

        # {[3]} Checkpoint: ledger lines stretch any staff
        self.caption("ledger", wait=False)
        extras = ((treble, "A5", "treble", xs[5]), (treble, "C6", "treble", xs[7]), (bass, "E2", "bass", xs[2]))
        ledger_notes = VGroup()
        for staff, pitch, clef, x in extras:
            note = _head(staff, pitch, x, clef=clef, named=True)
            ledger_notes.add(note)
            note[1].set_color(HIGHLIGHT)
            self.play(FadeIn(note, scale=1.2), run_time=0.3)
            add_pitches_sound(self, [pitch], duration=0.8)
            self.wait(0.8)
        self.wait(2.0)
        self.play(FadeOut(ledger_notes), run_time=0.4)

        # {[4]} Checkpoint: middle C belongs to both staves — pull them apart
        c_bass = c_treble.copy()
        self.add(c_bass)
        lift, drop = UP * 0.45, DOWN * 0.42
        self.caption("both", wait=False)
        self.play(
            FadeOut(c_label), FadeOut(left_bar), FadeOut(brace),
            VGroup(top_group, c_treble).animate.shift(lift),
            VGroup(low_group, c_bass).animate.shift(drop),
            run_time=1.0,
        )
        add_pitches_sound(self, ["C4"], duration=2.0)
        self.wait(4.6)

        # {[5]} Checkpoint: across the gap, one degree at a time
        self.play(FadeOut(c_treble), FadeOut(c_bass), run_time=0.4)
        notes = VGroup()
        for pitch, x in zip(walk, xs):
            on_bass = pitch[-1] == "3"
            notes.add(_head(bass if on_bass else treble, pitch, x, clef="bass" if on_bass else "treble", named=True))
        self.caption("across", wait=False)
        add_sequence_sound(self, walk, note_duration=1.0, qpm=60 / 0.55)
        for note in notes:
            self.play(FadeIn(note, scale=1.3), run_time=0.15)
            note.set_color(HIGHLIGHT)
            self.wait(0.4)
            note.set_color(INK)
        self.wait(0.6)
        add_sequence_sound(self, walk[::-1], note_duration=1.0, qpm=60 / 0.4)
        for note in notes[::-1]:
            note.set_color(HIGHLIGHT)
            self.wait(0.4)
            note.set_color(INK)
        self.wait(1.5)

        # {[6]} Checkpoint: remember
        self.remember()


class PartsOfANote(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a big staff
        self.title()
        ss = 0.6
        staff = Staff(width_ss=10.0, staff_space=ss)
        staff.move_to(np.array([-2.6, 0.4, 0.0]))
        clef = staff.clef("gClef", x_ss=0.8)
        self.play(FadeIn(staff), FadeIn(clef), run_time=0.5)

        # {[2]} Checkpoint: the head — its place gives the pitch
        head = Notehead("quarter", staff_space=ss)
        staff.place(head, 6.0, 3)
        label_x = staff.get_right()[0] + 1.6
        head_label = words(self.t("label-head"), 40, HIGHLIGHT)
        head_label.move_to(np.array([label_x, head.get_center()[1], 0.0]), aligned_edge=LEFT)
        head_arrow = Arrow(head_label.get_left() + LEFT * 0.1, head.get_right() + RIGHT * 0.1, buff=0.1, fill_color=HIGHLIGHT)
        self.caption("head", wait=False)
        self.play(FadeIn(head, scale=1.4), run_time=0.4)
        head.set_color(HIGHLIGHT)
        add_pitches_sound(self, ["A4"], duration=0.9)
        self.wait(1.0)
        self.play(head.animate.shift(UP * 2 * ss), run_time=0.5)  # up to E5
        add_pitches_sound(self, ["E5"], duration=0.9)
        self.wait(1.0)
        self.play(head.animate.shift(DOWN * 2 * ss), run_time=0.5)  # back to A4
        add_pitches_sound(self, ["A4"], duration=0.9)
        self.play(FadeIn(head_label), FadeIn(head_arrow), run_time=0.4)
        self.wait(1.6)
        head.set_color(INK)

        # {[3]} Checkpoint: the stem
        stem = stem_for(head, "up", color=HIGHLIGHT)
        stem_label = words(self.t("label-stem"), 40, HIGHLIGHT)
        stem_point = np.array([stem.get_right()[0] + 0.08, head.get_center()[1] + 1.2, 0.0])
        stem_label.move_to(np.array([label_x, stem_point[1], 0.0]), aligned_edge=LEFT)
        stem_arrow = Arrow(stem_label.get_left() + LEFT * 0.1, stem_point, buff=0.1, fill_color=HIGHLIGHT)
        self.caption("stem", wait=False)
        self.play(head_label.animate.set_color(INK), head_arrow.animate.set_fill(MUTED), run_time=0.2)
        self.play(GrowFromEdge(stem, DOWN), FadeIn(stem_label), FadeIn(stem_arrow), run_time=0.6)
        add_pitches_sound(self, ["A4"], duration=0.9)
        self.wait(2.4)
        stem.set_color(INK)

        # {[4]} Checkpoint: the flag — on the right of the stem
        flag = SmuflGlyph("flag8thUp", staff_space=ss, color=HIGHLIGHT)
        flag.shift(stem.get_corner(UP + LEFT) - flag.anchor_point("stemUpNW"))
        flag_label = words(self.t("label-flag"), 40, HIGHLIGHT)
        flag_point = np.array([flag.get_right()[0] + 0.05, flag.get_top()[1] - 0.55, 0.0])
        flag_label.move_to(np.array([label_x, head.get_center()[1] + 2.1, 0.0]), aligned_edge=LEFT)
        flag_arrow = Arrow(flag_label.get_left() + LEFT * 0.1, flag_point, buff=0.1, fill_color=HIGHLIGHT)
        self.caption("flag", wait=False)
        self.play(stem_label.animate.set_color(INK), stem_arrow.animate.set_fill(MUTED), run_time=0.2)
        self.play(FadeIn(flag, shift=LEFT * 0.2), FadeIn(flag_label), FadeIn(flag_arrow), run_time=0.5)
        add_pitches_sound(self, ["A4"], duration=0.45)
        self.wait(2.6)
        flag.set_color(INK)
        self.clear_stage()

        # {[5]} Checkpoint: five shapes, five lengths — each played, its bar growing
        values = (
            ("noteWhole", "name-whole", "uk-whole", 4.0),
            ("noteHalfUp", "name-half", "uk-half", 2.0),
            ("noteQuarterUp", "name-quarter", "uk-quarter", 1.0),
            ("note8thUp", "name-eighth", "uk-eighth", 0.5),
            ("note16thUp", "name-sixteenth", "uk-sixteenth", 0.25),
        )
        column_x = (-5.2, -2.6, 0.0, 2.6, 5.2)
        glyphs, names, uk_names, bars = VGroup(), VGroup(), VGroup(), VGroup()
        bar_full = 2.2
        for (glyph_name, name_key, uk_key, beats), x in zip(values, column_x):
            glyph = SmuflGlyph(glyph_name, staff_space=0.45)
            glyph.shift(np.array([x - 0.25, 0.9, 0.0]) - glyph.origin())
            glyphs.add(glyph)
            names.add(words(wrap(self.t(name_key), 7), LABEL_SIZE).move_to(np.array([x, 0.0, 0.0])))
            uk_names.add(words(self.t(uk_key), SMALL_SIZE, MUTED).move_to(np.array([x, -0.85, 0.0])))
            bar = Rectangle(
                width=bar_full * beats / 4, height=0.16,
                fill_color=BLUE, fill_opacity=0.6, stroke_width=0,
            )
            bar.move_to(np.array([x - bar_full / 2 + bar.get_width() / 2, -1.55, 0.0]))
            bars.add(bar)
        self.caption("shape", wait=False)
        seconds_per_beat = 0.6
        for glyph, name, bar, (_, _, _, beats) in zip(glyphs, names, bars, values):
            self.play(FadeIn(glyph, shift=UP * 0.2), FadeIn(name), run_time=0.35)
            glyph.set_color(HIGHLIGHT)
            add_pitches_sound(self, ["C5"], duration=beats * seconds_per_beat * 0.95)
            self.play(GrowFromEdge(bar, LEFT), run_time=beats * seconds_per_beat, rate_func=linear)
            glyph.set_color(INK)
            self.wait(0.35)
        self.wait(2.2)

        # {[6]} Checkpoint: the British names
        self.caption("british", wait=False)
        self.play(FadeIn(uk_names, shift=DOWN * 0.1), run_time=0.6)
        self.wait(5.5)

        # {[7]} Checkpoint: remember
        self.remember()


class StemDirection(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a climbing tune, its stems flipping
        self.title()
        pitches = ["F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5"]
        row = NoteRow(pitches, staff_space=0.44, spacing_ss=2.9)
        row.move_to(np.array([0.0, 0.5, 0.0]))
        middle = _line_glow(row.staff, 2, BLUE)
        self.play(FadeIn(row), run_time=0.5)
        play_row(self, row, pitches, seconds=0.45)
        self.play(FadeIn(middle), run_time=0.4)
        self.add(*[n for n in row.notes if n is not None])

        # {[2]} Checkpoint: below the middle line, stems go up on the right
        def show(indices, key):
            self.caption(key, wait=False)
            for i in indices:
                row.notes[i].set_color(HIGHLIGHT)
            add_sequence_sound(self, [pitches[i] for i in indices], note_duration=1.0, qpm=120)
            self.wait(reading_time(self.t(key)) + 0.6)
            for i in indices:
                row.notes[i].set_color(INK)

        show([0, 1, 2], "below")

        # {[3]} Checkpoint: above it, stems go down on the left
        show([4, 5, 6, 7], "above")

        # {[4]} Checkpoint: on the middle line: either; down is usual
        show([3], "middle")
        self.clear_stage()

        # {[5]} Checkpoint: flags curl right, stem up or down
        frow = NoteRow([None, None], staff_space=0.55, spacing_ss=6.0, left_margin_ss=6.0, right_margin_ss=3.0)
        frow.move_to(np.array([0.0, 0.5, 0.0]))
        up = frow.staff.place(SmuflGlyph("note8thUp", staff_space=0.55), 6.0, 2)
        down = frow.staff.place(SmuflGlyph("note8thDown", staff_space=0.55), 12.0, 6)
        self.play(FadeIn(frow), FadeIn(up), FadeIn(down), run_time=0.5)
        self.caption("flags", wait=False)
        for _ in range(2):
            for glyph, pitch in ((up, "G4"), (down, "D5")):
                glyph.set_color(HIGHLIGHT)
                add_pitches_sound(self, [pitch], duration=0.5)
                self.wait(0.8)
                glyph.set_color(INK)
        self.wait(1.8)
        self.clear_stage()

        # {[6]} Checkpoint: beamed groups share one direction
        xml = _rebeam(snippet("4/4 e8 g d' f g' e' a f'"), [(4, "up"), (4, "down")])
        score = engraved(xml, width=11.0, max_height=4.6, y=0.3)
        self.play(FadeIn(score), run_time=0.5)
        self.caption("beams", wait=False)
        spq = 0.6
        lit_play(self, score, example_events(xml, spq), spq)
        ids = [i for _, group in score.onset_note_ids() for i in group]
        odd = (ids[2], ids[6])  # D5 in a low group, A4 in a high group
        for note_id in odd:
            score.note(note_id).set_color(HIGHLIGHT)
        add_sequence_sound(self, ["D5", "A4"], note_duration=1.0, qpm=80)
        self.wait(3.5)

        # {[7]} Checkpoint: remember
        self.remember()

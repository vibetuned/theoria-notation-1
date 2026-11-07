"""Module 02 lessons (Gehrkens chs. II-III): half steps and spelling —
sharp, flat and natural; double sharps and flats (Rice's six rules); how
long an accidental lasts; enharmonic spellings; the key signature; and
the major-or-relative-minor test.

One idea per video; every word on screen comes from content/<lang>/.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/02-half-steps-and-spelling/scenes.py SharpFlatNatural -w -l
"""

import re

import numpy as np
from manimlib import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    ArcBetweenPoints,
    FadeIn,
    FadeOut,
    Rectangle,
    ReplacementTransform,
    VGroup,
)

from theoria.audio import add_chord_sequence_sound, add_events_sound, add_pitches_sound
from theoria.core.examples import snippet
from theoria.core.pitches import diatonic_steps_from
from theoria.notation.glyphs import Notehead, SmuflGlyph
from theoria.notation.lesson import (
    LABEL_SIZE,
    Keyboard,
    LessonScene,
    NoteRow,
    engraved,
    lit_play,
    play_row,
    reading_time,
    words,
)
from theoria.notation.staff import STAFF_REFERENCE, grand_staff_for, signature_glyphs
from theoria.theme import BACKGROUND, BLUE, HIGHLIGHT, INK

SPQ = 0.6  # seconds per quarter note in the engraved examples
STAFF_Y, KEYS_Y, KEYS_H = 1.25, -1.7, 1.3  # staff above, keyboard below


# -- local helpers -----------------------------------------------------------

def _x_ss(row: NoteRow, i: int) -> float:
    """Staff-space x of note i's head origin (its left edge)."""
    return (row.head(i).origin()[0] - row.staff.origin()[0]) / row.staff.staff_space


def _add_sign(row: NoteRow, i: int, glyph_name: str = "accidentalNatural") -> SmuflGlyph:
    """Draw an accidental NoteRow does not draw (a natural) before note i;
    it joins the note's group so it lights with it."""
    glyph = SmuflGlyph(glyph_name, staff_space=row.staff.staff_space)
    row.staff.place(glyph, _x_ss(row, i) - 1.6, row.steps[i])
    row.notes[i].add(glyph)
    return glyph


def _signs(row: NoteRow, i: int) -> VGroup:
    """The accidental glyphs inside note i's group."""
    return VGroup(*(m for m in row.notes[i] if isinstance(m, SmuflGlyph) and m.glyph_name.startswith("accidental")))


def _tidy_accidentals(row: NoteRow) -> NoteRow:
    """Set every accidental a fixed gap left of its head. NoteRow puts all
    of them 1.6 staff spaces back, so a wide double flat touches its head."""
    ss = row.staff.staff_space
    for i, group in enumerate(row.notes):
        if group is None:
            continue
        for sign in _signs(row, i):
            sign.shift(RIGHT * (group[0].get_left()[0] - 0.25 * ss - sign.get_right()[0]))
    return row


def _labels(row: NoteRow, texts: list[str | None], **kwargs) -> list:
    """row.labels_under, but indexed like the row (None at the gaps)."""
    group = iter(row.labels_under(texts, **kwargs))
    return [next(group) if text is not None and row.notes[i] is not None else None for i, text in enumerate(texts)]


def _sound_notes(scene, row: NoteRow, items, keyboard: Keyboard | None = None, seconds: float = 0.9, color=HIGHLIGHT):
    """Play (index, pitch) items one after another, lighting the note and
    its piano key while it sounds."""
    for i, pitch in items:
        row.notes[i].set_color(color)
        if keyboard is not None:
            keyboard.press(pitch, color)
        add_pitches_sound(scene, [pitch], duration=seconds * 0.95)
        scene.wait(seconds)
        row.notes[i].set_color(INK)
        if keyboard is not None:
            keyboard.release(pitch)


def _step_arc(keyboard: Keyboard, low: str, high: str, color=HIGHLIGHT) -> ArcBetweenPoints:
    a = keyboard.key(low).get_top() + UP * 0.12
    b = keyboard.key(high).get_top() + UP * 0.12
    return ArcBetweenPoints(a, b, angle=-2.4).set_stroke(color, width=7)


def _set_accidentals(xml: str, marks: list[str | None]) -> str:
    """Decide which notes of a snippet SHOW an accidental: music21 prints
    one on every altered note, but the barline lesson needs the second C
    sharp of a measure bare. `marks[i]` is a MusicXML accidental name
    ('sharp', 'natural') or None; the sounding pitch (<alter>) is kept."""
    notes = list(re.finditer(r"<note>.*?</note>", xml, re.S))
    out, last = [], 0
    for match, mark in zip(notes, marks):
        note = re.sub(r"\s*<accidental[^>]*>[^<]*</accidental>", "", match.group(0))
        if mark:
            # 'hidden:sharp' keeps a tie-stop note's accidental unprinted:
            # Verovio drops a tie whose start shows an accidental and whose
            # stop note has none
            attrs = ' print-object="no"' if mark.startswith("hidden:") else ""
            name = mark.removeprefix("hidden:")
            note = re.sub(r"(</type>(\s*<dot\s*/>)*)", rf"\1<accidental{attrs}>{name}</accidental>", note, count=1)
        out += [xml[last:match.start()], note]
        last = match.end()
    out.append(xml[last:])
    return "".join(out)


def _hide_accidental(score, note_id: str) -> None:
    """Make an engraved note's accidental invisible. Verovio prints the
    'hidden:' accidental anyway (it ignores print-object="no"), and a
    tied-over note must not repeat its sharp. The accidental is the
    leftmost visible part of the note's fragment."""
    parts = [
        m for m in score.note(note_id).family_members_with_points()
        if m.get_fill_opacity() > 0 or m.get_stroke_opacity() > 0
    ]
    parts = [m for m in parts if m.get_width() < 1.0]  # not the full-canvas sentinel
    parts.sort(key=lambda m: m.get_left()[0])
    if len(parts) > 1 and parts[0].get_right()[0] < parts[1].get_left()[0]:
        parts[0].set_fill(opacity=0).set_stroke(opacity=0)


def _events(notes: list[tuple[str, float]], spq: float = SPQ):
    """(pitch, quarters) in sequence -> (start s, pitches, duration s)."""
    events, t = [], 0.0
    for pitch, quarters in notes:
        events.append((t * spq, (pitch,), quarters * spq * 0.95))
        t += quarters
    return events


# -- lessons ------------------------------------------------------------------

class SharpFlatNatural(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a staff above, a keyboard below
        self.title()
        pitches = ["F4", "F#4", None, "B4", "B-4", "B4"]
        row = NoteRow(pitches, duration="whole", staff_space=0.42, spacing_ss=4.4)
        row.move_to(np.array([0.0, STAFF_Y, 0.0]))
        _add_sign(row, 5)
        _tidy_accidentals(row)
        names = _labels(row, 
            [self.t("name-f"), self.t("name-f-sharp"), None, self.t("name-b"), self.t("name-b-flat"), self.t("name-b")],
            size=36,
        )
        keyboard = Keyboard("C4", "C5", white_width=0.85, height=KEYS_H)
        keyboard.move_to(np.array([0.0, KEYS_Y, 0.0]))
        self.play(FadeIn(row.staff), FadeIn(row.clef), FadeIn(keyboard), run_time=0.6)

        # {[2]} Checkpoint: the half step — the very next key
        self.caption("half", wait=False)
        for low, high in (("E4", "F4"), ("F4", "F#4")):
            arc = _step_arc(keyboard, low, high)
            keyboard.press(low), keyboard.press(high)
            self.play(FadeIn(arc), run_time=0.3)
            add_events_sound(self, _events([(low, 1), (high, 1)], 0.7))
            self.wait(1.8)
            keyboard.release(low), keyboard.release(high)
            self.play(FadeOut(arc), run_time=0.3)
        self.wait(0.8)

        # {[3]} Checkpoint: F, then F sharp
        self.play(FadeIn(row.notes[0]), FadeIn(names[0]), run_time=0.4)
        _sound_notes(self, row, [(0, "F4")], keyboard)
        self.caption("sharp", wait=False)
        sharp = _signs(row, 1)
        self.play(FadeIn(row.notes[1], shift=RIGHT * 0.2), FadeIn(names[1]), run_time=0.5)
        self.play(sharp.animate.set_color(HIGHLIGHT).scale(1.3), run_time=0.3)
        self.play(sharp.animate.set_color(INK).scale(1 / 1.3), run_time=0.3)
        _sound_notes(self, row, [(0, "F4"), (1, "F#4")], keyboard)
        self.wait(1.6)

        # {[4]} Checkpoint: same space on the staff, a different pitch
        ss = row.staff.staff_space
        x0, x1 = row.notes[0].get_left()[0] - 0.25, row.notes[1].get_right()[0] + 0.25
        band = Rectangle(width=x1 - x0, height=ss * 0.9, fill_color=BLUE, fill_opacity=0.25, stroke_width=0)
        band.move_to(np.array([(x0 + x1) / 2, row.head(0).get_center()[1], 0.0]))
        self.caption("same-place", wait=False)
        self.play(FadeIn(band), run_time=0.4)
        _sound_notes(self, row, [(0, "F4"), (1, "F#4")], keyboard)
        self.wait(2.6)
        self.play(FadeOut(band), run_time=0.3)

        # {[5]} Checkpoint: B, then B flat
        self.caption("flat", wait=False)
        self.play(FadeIn(row.notes[3]), FadeIn(names[3]), run_time=0.4)
        _sound_notes(self, row, [(3, "B4")], keyboard)
        self.play(FadeIn(row.notes[4], shift=RIGHT * 0.2), FadeIn(names[4]), run_time=0.5)
        _sound_notes(self, row, [(3, "B4"), (4, "B-4")], keyboard)
        self.wait(1.6)

        # {[6]} Checkpoint: the natural cancels it
        self.caption("natural", wait=False)
        self.play(FadeIn(row.notes[5], shift=RIGHT * 0.2), FadeIn(names[5]), run_time=0.5)
        _sound_notes(self, row, [(4, "B-4"), (5, "B4")], keyboard)
        self.wait(2.0)

        # {[7]} Checkpoint: remember
        self.remember()


class DoubleSharpsAndFlats(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; staff and keyboard
        self.title()
        keyboard = Keyboard("C4", "C5", white_width=0.85, height=KEYS_H)
        keyboard.move_to(np.array([0.0, KEYS_Y, 0.0]))

        def ladder(pitches, key):
            row = NoteRow(pitches, duration="whole", staff_space=0.44, spacing_ss=4.4, left_margin_ss=6.5)
            row.move_to(np.array([0.0, STAFF_Y, 0.0]))
            _tidy_accidentals(row)
            self.play(FadeIn(row.staff), FadeIn(row.clef), run_time=0.4)
            self.caption(key, wait=False)
            for i, pitch in enumerate(pitches):
                self.play(FadeIn(row.notes[i], shift=RIGHT * 0.2), run_time=0.35)
                _sound_notes(self, row, [(i, pitch)], keyboard, seconds=0.8)
            self.play(_signs(row, 2).animate.set_color(HIGHLIGHT), run_time=0.3)
            _sound_notes(self, row, [(0, pitches[0]), (2, pitches[2])], keyboard, seconds=1.0)
            keyboard.press(pitches[2], HIGHLIGHT)
            self.wait(2.4)
            keyboard.release(pitches[2])
            self.play(FadeOut(row), run_time=0.4)

        self.play(FadeIn(keyboard), run_time=0.4)

        # {[2]} Checkpoint: F, F sharp, F double sharp — the G key
        ladder(["F4", "F#4", "F##4"], "double-sharp")

        # {[3]} Checkpoint: B, B flat, B double flat — the A key
        ladder(["B4", "B-4", "B--4"], "double-flat")
        self.clear_stage()

        # {[4]} Checkpoint: Rice's rules, raising: plain->sharp, sharp->double sharp, flat->natural
        raise_pitches = ["D4", "D#4", None, "F#4", "F##4", None, "B-4", "B4"]
        lower_pitches = ["E4", "E-4", None, "B-4", "B--4", None, "F#4", "F4"]
        rows = []
        for pitches, y in ((raise_pitches, 1.6), (lower_pitches, -1.0)):
            row = NoteRow(pitches, duration="whole", staff_space=0.34, spacing_ss=3.3)
            row.shift(np.array([0.55, y, 0.0]) - row.staff.get_center())
            _add_sign(row, 7)
            rows.append(_tidy_accidentals(row))
        labels = VGroup(
            words(self.t("label-raise"), 36, BLUE).next_to(rows[0], LEFT, buff=0.35),
            words(self.t("label-lower"), 36, BLUE).next_to(rows[1], LEFT, buff=0.35),
        )
        self.play(FadeIn(rows[0]), FadeIn(labels[0]), run_time=0.5)
        self.caption("raise", wait=False)
        for a, b in ((0, 1), (3, 4), (6, 7)):
            _sound_notes(self, rows[0], [(a, raise_pitches[a]), (b, raise_pitches[b])], seconds=0.75)
            self.wait(0.3)
        self.wait(1.2)

        # {[5]} Checkpoint: lowering: plain->flat, flat->double flat, sharp->natural
        self.play(FadeIn(rows[1]), FadeIn(labels[1]), run_time=0.5)
        self.caption("lower", wait=False)
        for a, b in ((0, 1), (3, 4), (6, 7)):
            _sound_notes(self, rows[1], [(a, lower_pitches[a]), (b, lower_pitches[b])], seconds=0.75)
            self.wait(0.3)
        self.wait(1.5)

        # {[6]} Checkpoint: remember
        self.remember()


class AccidentalsAndBarLines(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; two measures, the sharp written once
        self.title()
        base = snippet("3/4 c'#4 d' c'# c' b a")
        plain = _set_accidentals(base, ["sharp", None, None, None, None, None])
        notes = [("C#5", 1), ("D5", 1), ("C#5", 1), ("C5", 1), ("B4", 1), ("A4", 1)]
        score = engraved(plain, width=12.0, max_height=5.2, y=0.45)
        self.play(FadeIn(score), run_time=0.5)
        lit_play(self, score, _events(notes), SPQ)
        ids = [group[0] for _, group in score.onset_note_ids()]

        def light(score_, note_ids, pitches, seconds=0.9):
            for note_id, pitch in zip(note_ids, pitches):
                score_.note(note_id).set_color(HIGHLIGHT)
                add_pitches_sound(self, [pitch], duration=seconds * 0.95)
                self.wait(seconds)
                score_.note(note_id).set_color(INK)

        # {[2]} Checkpoint: the sharp lasts to the end of its measure
        self.caption("measure", wait=False)
        light(score, [ids[0], ids[2]], ["C#5", "C#5"])
        score.note(ids[2]).set_color(HIGHLIGHT)
        self.wait(reading_time(self.t("measure")) - 1.0)
        score.note(ids[2]).set_color(INK)

        # {[3]} Checkpoint: the bar line cancels it
        self.caption("barline", wait=False)
        light(score, [ids[2], ids[3]], ["C#5", "C5"])
        score.note(ids[3]).set_color(HIGHLIGHT)
        self.wait(reading_time(self.t("barline")) - 1.0)
        score.note(ids[3]).set_color(INK)

        # {[4]} Checkpoint: a courtesy natural — same sound, no doubt
        polite = _set_accidentals(base, ["sharp", None, None, "natural", None, None])
        score2 = engraved(polite, width=12.0, max_height=5.2, y=0.45)
        ids2 = [group[0] for _, group in score2.onset_note_ids()]
        score2.note(ids2[3]).set_color(HIGHLIGHT)
        self.caption("courtesy", wait=False)
        self.play(FadeOut(score), FadeIn(score2), run_time=0.6)
        add_pitches_sound(self, ["C5"], duration=1.0)
        self.wait(reading_time(self.t("courtesy")) + 0.5)
        score2.note(ids2[3]).set_color(INK)
        self.clear_caption()
        self.play(FadeOut(score2), run_time=0.4)

        # {[5]} Checkpoint: a tie carries the sharp over the bar line
        tied_xml = _set_accidentals(snippet("3/4 g2 c'#4~ c'#4 d' c'"), [None, "sharp", "hidden:sharp", None, "natural"])
        tied = engraved(tied_xml, width=12.0, max_height=5.2, y=0.45)
        _hide_accidental(tied, tied.note_ids[2])  # the tied-over C sharp
        self.play(FadeIn(tied), run_time=0.5)
        tied_notes = [("G4", 2), ("C#5", 2), ("D5", 1), ("C5", 1)]
        lit_play(self, tied, _events(tied_notes), SPQ)
        every = tied.note_ids  # document order: G4, C#5, C#5 (tied), D5, C5
        self.caption("tie", wait=False)
        for _ in range(2):
            tied.note(every[1]).set_color(HIGHLIGHT)
            tied.note(every[2]).set_color(HIGHLIGHT)
            add_pitches_sound(self, ["C#5"], duration=2 * SPQ * 1.5)
            self.wait(2 * SPQ * 1.5 + 0.4)
            tied.note(every[1]).set_color(INK)
            tied.note(every[2]).set_color(INK)
            self.wait(0.3)
        self.wait(1.5)

        # {[6]} Checkpoint: after the tie, plain C again
        self.caption("after-tie", wait=False)
        for _ in range(2):
            for note_ids, pitch in (((every[1], every[2]), "C#5"), ((every[4],), "C5")):
                for note_id in note_ids:
                    tied.note(note_id).set_color(HIGHLIGHT)
                add_pitches_sound(self, [pitch], duration=0.85)
                self.wait(0.9)
                for note_id in note_ids:
                    tied.note(note_id).set_color(INK)
        self.wait(1.2)

        # {[7]} Checkpoint: remember
        self.remember()


class EnharmonicSpelling(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; three pairs of spellings, a keyboard
        self.title()
        pitches = ["F#4", "G-4", "E#4", "F4", "C-5", "B4"]
        row = NoteRow(pitches, duration="whole", staff_space=0.42, spacing_ss=4.2)
        row.move_to(np.array([0.0, STAFF_Y, 0.0]))
        _tidy_accidentals(row)
        # one baseline just under the staff (labels_under would sink them
        # below E sharp's long sharp sign, onto the keyboard)
        label_y = row.staff.get_bottom()[1] - 0.6
        names = [
            words(self.t(k), 36).move_to(np.array([row.note_x(i), label_y, 0.0]))
            for i, k in enumerate(("name-f-sharp", "name-g-flat", "name-e-sharp", "name-f", "name-c-flat", "name-b"))
        ]
        brackets = VGroup()
        for a in (0, 2, 4):
            x0, x1 = names[a].get_left()[0] - 0.1, names[a + 1].get_right()[0] + 0.1
            y = min(names[a].get_bottom()[1], names[a + 1].get_bottom()[1]) - 0.15
            brackets.add(Rectangle(width=x1 - x0, height=0.05, fill_color=BLUE, fill_opacity=1, stroke_width=0).move_to(np.array([(x0 + x1) / 2, y, 0.0])))
        keyboard = Keyboard("C4", "C5", white_width=0.85, height=KEYS_H)
        keyboard.move_to(np.array([0.0, KEYS_Y, 0.0]))
        self.play(FadeIn(row.staff), FadeIn(row.clef), FadeIn(keyboard), run_time=0.6)

        def pair(a):
            b = a + 1
            self.play(
                FadeIn(row.notes[a]), FadeIn(row.notes[b]), FadeIn(names[a]), FadeIn(names[b]), FadeIn(brackets[a // 2]),
                run_time=0.4,
            )
            for _ in range(2):
                _sound_notes(self, row, [(a, pitches[a]), (b, pitches[b])], keyboard, seconds=0.85)

        # {[2]} Checkpoint: F sharp and G flat — one key
        self.caption("pair", wait=False)
        pair(0)
        self.wait(1.0)

        # {[3]} Checkpoint: white keys have spare names: E sharp = F, C flat = B
        self.caption("white", wait=False)
        pair(2)
        pair(4)
        self.wait(1.0)

        # {[4]} Checkpoint: enharmonic — one sound, two spellings
        self.caption("term", wait=False)
        for a in (0, 2, 4):
            b = a + 1
            row.notes[a].set_color(BLUE), row.notes[b].set_color(BLUE)
            keyboard.press(pitches[a], BLUE)
            add_pitches_sound(self, [pitches[a]], duration=0.8)
            self.wait(1.0)
            row.notes[a].set_color(INK), row.notes[b].set_color(INK)
            keyboard.release(pitches[a])
        self.wait(1.8)

        # {[5]} Checkpoint: remember
        self.remember()


class KeySignatures(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a tune with every F sharp written out
        self.title()
        tune = ["D5", "F#5", "E5", "D5", "C5", "B4", "A4", "F#4", "G4"]
        row = NoteRow(tune, staff_space=0.42, spacing_ss=2.45, left_margin_ss=7.3)
        row.move_to(np.array([0.0, 0.6, 0.0]))
        _tidy_accidentals(row)
        self.play(FadeIn(row), run_time=0.5)
        play_row(self, row, tune, seconds=0.5)

        # {[2]} Checkpoint: both F's need the sharp
        self.caption("tune", wait=False)
        sharps = VGroup(_signs(row, 1), _signs(row, 7))
        self.play(sharps.animate.set_color(HIGHLIGHT), run_time=0.3)
        _sound_notes(self, row, [(1, "F#5"), (7, "F#4")], seconds=0.9)
        self.wait(2.0)

        # {[3]} Checkpoint: the signature writes the sharp once, after the clef
        signature = signature_glyphs(row.staff, "G", x_start=4.1).set_color(HIGHLIGHT)
        self.caption("signature", wait=False)
        self.play(ReplacementTransform(sharps, signature), run_time=1.2)
        for i in (1, 7):  # the sharps now live in the signature only
            row.notes[i].remove(*[m for m in row.notes[i] if isinstance(m, SmuflGlyph) and m.glyph_name.startswith("accidental")])
        self.wait(reading_time(self.t("signature")))

        # {[4]} Checkpoint: one sharp on the F line means every F
        line = row.staff.lines[4]
        glow = Rectangle(width=line.get_width(), height=row.staff.staff_space * 0.16, fill_color=HIGHLIGHT, fill_opacity=1, stroke_width=0).move_to(line)
        self.caption("every", wait=False)
        self.play(FadeIn(glow), run_time=0.3)
        self.wait(1.2)
        self.play(FadeOut(glow), run_time=0.3)
        _sound_notes(self, row, [(1, "F#5"), (7, "F#4")], seconds=1.0)
        self.wait(2.2)
        signature.set_color(INK)

        # {[5]} Checkpoint: same notes, same sound
        self.caption("same", wait=False)
        play_row(self, row, tune, seconds=0.5)
        self.wait(1.5)

        # {[6]} Checkpoint: remember
        self.remember()


def _chord(staves: dict, pitches: list[str], x_ss: float, signature_letters: set[str] = frozenset()) -> VGroup:
    """Whole-note chord on a grand staff: the lower two pitches on the bass
    staff, the upper two on the treble. Accidentals are drawn unless the
    key signature already carries them (`signature_letters`, sharps)."""
    group = VGroup()
    for index, pitch in enumerate(pitches):
        clef = "bass" if index < 2 else "treble"
        staff = staves[clef]
        step = diatonic_steps_from(pitch, STAFF_REFERENCE[clef])
        head = Notehead("whole", staff_space=staff.staff_space)
        staff.place(head, x_ss, step)
        group.add(head, staff.ledger_lines(x_ss, step, head_width_ss=1.3))
        if "#" in pitch and pitch[0] not in signature_letters:
            sign = SmuflGlyph("accidentalSharp", staff_space=staff.staff_space)
            group.add(staff.place(sign, x_ss - 1.5, step))
    return group


class MajorOrMinor(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a grand staff with one sharp
        self.title()
        staves, xs = grand_staff_for(5, base_staff_space=0.3, treble_y=1.45, bass_y=-1.55, clef_margin_ss=9.0)
        ss = staves["treble"].staff_space
        clefs = VGroup(staves["treble"].clef("gClef", x_ss=1.0), staves["bass"].clef("fClef", x_ss=1.0))
        sig_t = signature_glyphs(staves["treble"], "G", x_start=4.2)
        sig_b = signature_glyphs(staves["bass"], "G", x_start=4.2).shift(DOWN * ss)  # F3: 4th line
        top, bottom = staves["treble"].get_top()[1], staves["bass"].get_bottom()[1]
        left_x = staves["treble"].get_left()[0]
        left_bar = Rectangle(width=0.03, height=top - bottom, fill_color=INK, fill_opacity=1, stroke_width=0)
        left_bar.move_to(np.array([left_x, (top + bottom) / 2, 0.0]))
        brace = SmuflGlyph("brace", staff_space=ss)
        brace.stretch_to_fit_height(top - bottom).next_to(left_bar, LEFT, buff=0.06)
        mid_x = staves["treble"].point_for(xs[2], 0)[0]
        double_bar = VGroup(
            Rectangle(width=0.03, height=top - bottom, fill_color=INK, fill_opacity=1, stroke_width=0).move_to(np.array([mid_x - 0.09, (top + bottom) / 2, 0])),
            Rectangle(width=0.09, height=top - bottom, fill_color=INK, fill_opacity=1, stroke_width=0).move_to(np.array([mid_x + 0.05, (top + bottom) / 2, 0])),
        )
        frame = VGroup(staves["treble"], staves["bass"], clefs, left_bar, brace, double_bar)
        self.play(FadeIn(frame), FadeIn(sig_t), FadeIn(sig_b), run_time=0.6)

        # {[2]} Checkpoint: one sharp: G major, and also E minor
        self.caption("shared", wait=False)
        self.play(sig_t.animate.set_color(HIGHLIGHT), sig_b.animate.set_color(HIGHLIGHT), run_time=0.4)
        self.wait(reading_time(self.t("shared")))
        self.play(sig_t.animate.set_color(INK), sig_b.animate.set_color(INK), run_time=0.3)

        # {[3]} Checkpoint: two endings drawn; the test — the last bass note
        major = ([["D3", "A3", "D4", "F#4"], ["G2", "B3", "D4", "G4"]], xs[0], xs[1])
        minor = ([["B2", "B3", "D#4", "F#4"], ["E3", "B3", "E4", "G4"]], xs[3], xs[4])
        drawn = []
        for chords, xa, xb in (major, minor):
            drawn.append((_chord(staves, chords[0], xa, {"F"}), _chord(staves, chords[1], xb, {"F"})))
        self.play(*(FadeIn(chord) for pair in drawn for chord in pair), run_time=0.6)
        self.caption("test", wait=False)
        finals = VGroup(drawn[0][1][0], drawn[1][1][0])  # the bass heads of the last chords
        self.play(finals.animate.set_color(BLUE).scale(1.3), run_time=0.4)
        self.play(finals.animate.scale(1 / 1.3), run_time=0.3)
        self.wait(reading_time(self.t("test")))
        finals.set_color(INK)

        def cadence(spec, pair, label_key, solfa_key, caption_key):
            chords, xa, xb = spec
            first, last = pair
            name = words(self.t(label_key), LABEL_SIZE, INK, weight="BOLD")
            center_x = (staves["treble"].point_for(xa, 0)[0] + staves["treble"].point_for(xb, 0)[0]) / 2 + 0.25
            name.move_to(np.array([center_x, top + 0.42, 0.0]))
            self.caption(caption_key, wait=False)
            for _ in range(2):
                add_chord_sequence_sound(self, chords, chord_duration=1.3, qpm=60)
                first.set_color(HIGHLIGHT)
                self.wait(1.3)
                first.set_color(INK)
                last.set_color(HIGHLIGHT)
                self.wait(1.5)
                last.set_color(INK)
                self.wait(0.3)
            bass_note = last[0]
            bass_note.set_color(HIGHLIGHT)
            text = words(self.t(solfa_key), 36, HIGHLIGHT, weight="BOLD")
            backing = Rectangle(
                width=text.get_width() + 0.16, height=text.get_height() + 0.1,
                fill_color=BACKGROUND, fill_opacity=1, stroke_width=0,
            )
            solfa = VGroup(backing, text).next_to(bass_note, LEFT, buff=0.25)
            self.play(FadeIn(name), FadeIn(solfa), run_time=0.4)
            add_pitches_sound(self, [chords[1][0]], duration=1.5)
            self.wait(2.2)
            return solfa

        # {[4]} Checkpoint: ending on G — G major (do)
        do = cadence(major, drawn[0], "label-major", "label-do", "major")

        # {[5]} Checkpoint: ending on E — E minor (la)
        la = cadence(minor, drawn[1], "label-minor", "label-la", "minor")

        # {[6]} Checkpoint: do and la
        self.caption("solfa", wait=False)
        for mob in (do, la):
            self.play(mob.animate.scale(1.25), run_time=0.3)
            self.play(mob.animate.scale(1 / 1.25), run_time=0.3)
        self.wait(reading_time(self.t("solfa")))

        # {[7]} Checkpoint: remember
        self.remember()

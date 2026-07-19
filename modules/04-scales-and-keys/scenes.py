"""Module 04 lessons (Gehrkens chs. VII-VIII): scales and keys — every
major scale, then every minor in its three forms, each shown twice: the
key signature at the clef, and the same scale spelled with accidentals.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/04-scales-and-keys/scenes.py AllTheMajorScales -w -l
"""

from manimlib import DOWN, UP, FadeIn, FadeOut, Scene, Text, VGroup, Write

from music21 import scale as m21_scale

from theoria.audio import add_pitches_sound
from theoria.core.pitches import diatonic_steps_from
from theoria.notation.glyphs import Notehead, SmuflGlyph
from theoria.notation.staff import (
    ACCIDENTAL_GLYPHS,
    Staff,
    signature_glyphs,
)
from theoria.theme import BLUE, HIGHLIGHT, INK, MUTED

# Gehrkens' fifteen positions of the one major scale (ch. VII), sharps
# then flats, and their relative minors (ch. VIII)
MAJOR_TONICS = (
    "C", "G", "D", "A", "E", "B", "F#", "C#",
    "F", "B-", "E-", "A-", "D-", "G-", "C-",
)
MINOR_TONICS = (
    "a", "e", "b", "f#", "c#", "g#", "d#", "a#",
    "d", "g", "c", "f", "b-", "e-", "a-",
)


def _key_label(tonic: str) -> str:
    name = tonic.replace("-", "♭").replace("#", "♯")
    if tonic[0].islower():
        return f"{name[0].upper()}{name[1:]} minor"
    return f"{name} major"


def _scale_pitches(tonic: str, form=None) -> list[str]:
    upper = tonic[0].upper() + tonic[1:]
    octave = 4 if upper[0] in "CDEFG" else 3
    scale_class = form or (
        m21_scale.MinorScale if tonic[0].islower() else m21_scale.MajorScale
    )
    return [
        p.nameWithOctave
        for p in scale_class(upper).getPitches(
            f"{upper}{octave}", f"{upper}{octave + 1}"
        )
    ]


def _staff(width_ss: float, staff_space: float, y: float, x: float = 0.0) -> Staff:
    staff = Staff(width_ss=width_ss, staff_space=staff_space)
    staff.center()
    staff.shift((x, y, 0.0))
    return staff


def _note_at(staff: Staff, pitch: str, x_ss: float, color=INK):
    """A quarter notehead (with its accidental, when the pitch carries
    one) at a staff position; returns (head, extras)."""
    step = diatonic_steps_from(pitch, "E4")
    extras = VGroup(staff.ledger_lines(x_ss, step))
    head = Notehead("quarter", staff_space=staff.staff_space)
    staff.place(head, x_ss, step)
    head.set_color(color)
    accidental = ACCIDENTAL_GLYPHS.get(pitch[1] if len(pitch) > 2 else "")
    if accidental:
        glyph = SmuflGlyph(accidental, staff_space=staff.staff_space)
        staff.place(glyph, x_ss - 1.2, step)
        glyph.set_color(color)
        extras.add(glyph)
    return head, extras


def _draw_scale_row(scene, staff, pitches, x_start=6.0, x_step=1.9,
                    per_note=0.32, hold_last=0.6):
    """Draw a scale left to right on `staff`, sounding each note as it
    appears; accidentals travel with their notes. Returns the group."""
    group = VGroup()
    for i, pitch in enumerate(pitches):
        head, extras = _note_at(staff, pitch, x_start + i * x_step)
        head.set_color(HIGHLIGHT)
        add_pitches_sound(
            scene, [pitch], duration=per_note + (hold_last if i == len(pitches) - 1 else 0.05)
        )
        scene.play(FadeIn(VGroup(head, extras)), run_time=per_note)
        head.set_color(INK)
        group.add(head, extras)
    scene.wait(hold_last)
    return group


def _signature_display(scene, tonic, y=2.35):
    """A short staff with clef + the key's signature + its name."""
    staff = _staff(15.0, 0.22, y, x=-3.4)
    clef = staff.clef("gClef")
    signature = signature_glyphs(staff, tonic)
    label = Text(_key_label(tonic), font_size=32, color=BLUE)
    label.next_to(staff, buff=0.6)
    group = VGroup(staff, clef, signature, label)
    scene.play(FadeIn(group), run_time=0.5)
    return group


class AllTheMajorScales(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("All fifteen major scales", font_size=40).to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "above: what the SIGNATURE says — below: the same scale spelled out, accidental by accidental",
            font_size=21,
            color=MUTED,
        )
        caption.to_edge(DOWN, buff=0.6)
        self.play(FadeIn(caption))

        # {[2]} Checkpoint: each key — signature above, spelled scale below
        for tonic in MAJOR_TONICS:
            signature = _signature_display(self, tonic)
            staff = _staff(34.0, 0.26, 0.3)
            clef = staff.clef("gClef")
            self.play(FadeIn(VGroup(staff, clef)), run_time=0.35)
            notes = _draw_scale_row(self, staff, _scale_pitches(tonic))
            self.play(FadeOut(VGroup(signature, staff, clef, notes)), run_time=0.4)

        # {[3]} Checkpoint: the closing thought
        closing = Text(
            "one pattern, fifteen addresses — the signature is just the pattern, written once",
            font_size=23,
            color=INK,
        )
        closing.to_edge(DOWN, buff=0.6)
        self.play(FadeOut(caption), FadeIn(closing))
        self.wait(2.2)


class AllTheMinorScales(Scene):
    def construct(self):
        # {[1]} Checkpoint: title
        title = Text("All fifteen minor scales, three forms each", font_size=38)
        title.to_edge(UP)
        self.play(Write(title))
        caption = Text(
            "primitive first, then harmonic (raised 7), then melodic (6 and 7 raised ascending)",
            font_size=21,
            color=MUTED,
        )
        caption.to_edge(DOWN, buff=0.55)
        self.play(FadeIn(caption))

        forms = (
            ("primitive", m21_scale.MinorScale),
            ("harmonic", m21_scale.HarmonicMinorScale),
            ("melodic", m21_scale.MelodicMinorScale),
        )
        rows_y = (1.35, -0.45, -2.25)

        from manimlib import LEFT

        # {[2]} Checkpoint: each key — signature above, the three forms below
        for tonic in MINOR_TONICS:
            signature = _signature_display(self, tonic, y=2.45)
            shown = VGroup(signature)
            for (form_name, form_class), y in zip(forms, rows_y):
                staff = _staff(34.0, 0.24, y)
                clef = staff.clef("gClef")
                form_label = Text(form_name, font_size=20, color=BLUE)
                form_label.next_to(staff, LEFT, buff=0.3)
                self.play(FadeIn(VGroup(staff, clef, form_label)), run_time=0.3)
                notes = _draw_scale_row(
                    self,
                    staff,
                    _scale_pitches(tonic, form_class),
                    per_note=0.3,
                    hold_last=0.35,
                )
                shown.add(staff, clef, form_label, notes)
            self.wait(0.4)
            self.play(FadeOut(shown), run_time=0.4)

        # {[3]} Checkpoint: the closing law
        closing = Text(
            "whatever rises, rises as an ACCIDENTAL — the signature belongs to the primitive form",
            font_size=22,
            color=INK,
        )
        closing.to_edge(DOWN, buff=0.55)
        self.play(FadeOut(caption), FadeIn(closing))
        self.wait(2.2)

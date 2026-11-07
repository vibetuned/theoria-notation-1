"""Module 03 lessons (Gehrkens chs. X-XII): time — rhythm, measure and
tempo told apart; strong beats and syncopation; simple and compound
meter; common and cut time; the tempo words and the metronome; and the
words that change the tempo along the way.

One idea per video; every word on screen comes from content/<lang>/.
Accents are AUDIBLE: `_accented_sound` renders note velocities, which
the kit's audio helpers do not carry.

Render:
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/03-time/scenes.py RhythmMeasureTempo -w -l
"""

import hashlib
import subprocess

import numpy as np
from manimlib import (
    DOWN,
    ITALIC,
    LEFT,
    RIGHT,
    UP,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    Text,
    Transform,
    VGroup,
)

from theoria.audio import add_events_sound
from theoria.core.examples import snippet
from theoria.notation.glyphs import SmuflGlyph
from theoria.notation.lesson import (
    LessonScene,
    NoteRow,
    engraved,
    lit_play,
    reading_time,
    words,
)
from theoria.notation.staff import Staff
from theoria.paths import DEFAULT_SOUNDFONT, MEDIA_DIR
from theoria.theme import BLUE, FONT, HIGHLIGHT, INK, MUTED, RED

STRONG, MEDIUM, WEAK = 112, 86, 52  # MIDI velocities
TICK = "C7"  # a quiet high tick marks every beat


# -- local helpers -------------------------------------------------------------

def _midi(name: str) -> int:
    """'C#5' -> 73 (music21 spelling: '#' sharp, '-' flat)."""
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[name[0]]
    alter = name.count("#") - name.count("-")
    return 12 * (int(name[-1]) + 1) + base + alter


def _accented_sound(scene, events, qpm: float = 60.0) -> None:
    """Like add_events_sound, but each event carries a MIDI velocity:
    (start, pitches, duration, velocity), times in quarters at `qpm`.
    Rendered mido -> .mid -> FluidSynth, cached by content."""
    import mido

    digest = hashlib.md5(repr(("accented", events, qpm)).encode()).hexdigest()[:16]
    wav = MEDIA_DIR / "audio" / f"accented-{digest}.wav"
    if not wav.exists():
        wav.parent.mkdir(parents=True, exist_ok=True)
        tpb = 480
        messages = []
        for start, pitches, duration, velocity in events:
            for pitch in pitches:
                note = _midi(pitch)
                messages.append((round(start * tpb), 1, mido.Message("note_on", note=note, velocity=velocity)))
                messages.append((round((start + duration) * tpb), 0, mido.Message("note_off", note=note, velocity=0)))
        messages.sort(key=lambda m: (m[0], m[1]))
        track = mido.MidiTrack([mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(qpm))])
        now = 0
        for tick, _, message in messages:
            track.append(message.copy(time=tick - now))
            now = tick
        midi = mido.MidiFile(ticks_per_beat=tpb)
        midi.tracks.append(track)
        midi_path = wav.with_suffix(".mid")
        midi.save(midi_path)
        subprocess.run(
            ["fluidsynth", "-ni", "-g", "0.8", "-r", "44100", "-F", str(wav), str(DEFAULT_SOUNDFONT), str(midi_path)],
            check=True, capture_output=True,
        )
    scene.add_sound(str(wav))


def _visible(mob) -> list:
    """Drawn parts of an engraved fragment (not its full-canvas sentinel)."""
    return [
        m for m in mob.family_members_with_points()
        if (m.get_fill_opacity() > 0 or m.get_stroke_opacity() > 0)
    ]


def _content_box(score) -> tuple[float, float]:
    """(bottom, top) of everything actually drawn in an engraved score."""
    parts = [m for m in _visible(score) if m.get_height() < score.get_height() * 0.9]
    return min(m.get_bottom()[1] for m in parts), max(m.get_top()[1] for m in parts)


def _note_top(score, note_id: str) -> float:
    return max(m.get_top()[1] for m in _visible(score.note(note_id)) if m.get_height() < 2.0)


def _head_x(score, note_id: str) -> float:
    """Scene x of a note's head, measured from what is drawn. (The kit's
    EngravedScore.note_scene_x reads ~6.6% of the score width too far
    left, so counts placed with it drift off their notes.) The head is
    the flattest drawn part wider than a stem: accidentals, flags and
    dots are taller or smaller."""
    parts = [m for m in _visible(score.note(note_id)) if m.get_width() > 0.12 and m.get_height() < 2.0]
    head = min(parts, key=lambda m: m.get_height() / m.get_width())
    return head.get_center()[0]


def _onset_x(score) -> dict[float, float]:
    """Quarter position -> scene x of the notes starting there."""
    return {
        round(q, 4): sum(_head_x(score, i) for i in ids) / len(ids)
        for q, ids in score.onset_note_ids()
    }


def _beat_xs(score, n_beats: int, beat_q: float = 1.0, end_q: float | None = None) -> list[float]:
    """x of every beat, sounded or not: an onset's x when a note starts on
    the beat, otherwise interpolated between the neighbouring onsets (and
    the final bar line, at quarter `end_q`, when given)."""
    xs = _onset_x(score)
    if end_q is not None:
        right = max(m.get_right()[0] for m in _visible(score.background) if m.get_height() < score.get_height() * 0.9)
        xs[round(end_q, 4)] = right - 0.35
    qs = sorted(xs)
    out = []
    for b in range(n_beats):
        q = round(b * beat_q, 4)
        if q in xs:
            out.append(xs[q])
            continue
        before = max((k for k in qs if k < q), default=qs[0])
        after = min((k for k in qs if k > q), default=None)
        if after is None:  # past the last onset: keep the last spacing
            step = (xs[qs[-1]] - xs[qs[-2]]) / (qs[-1] - qs[-2]) if len(qs) > 1 else 0.5
            out.append(xs[before] + (q - before) * step)
        else:
            out.append(xs[before] + (xs[after] - xs[before]) * (q - before) / (after - before))
    return out


def _counts(xs, y: float, per_measure: int, colors=None, size: float = 36) -> VGroup:
    group = VGroup()
    for i, x in enumerate(xs):
        n = i % per_measure + 1
        color = colors(n) if colors else MUTED
        group.add(words(str(n), size, color).move_to(np.array([x, y, 0.0])))
    return group


def _walk(scene, score, counts, base_colors, notes, first_q, last_q, spq, velocity_of, tick=True):
    """Sound notes (start q, pitch, length q) between first_q and last_q
    with accent velocities, and walk the beat counts: each count lights
    on its beat, each note at its onset."""
    chosen = [(s, p, d) for s, p, d in notes if first_q <= s < last_q]
    events = [(s - first_q, (p,), d * 0.95, velocity_of(s, d)) for s, p, d in chosen]
    if tick:
        events += [(b - first_q, (TICK,), 0.1, 34) for b in range(int(first_q), int(last_q))]
    _accented_sound(scene, events, qpm=60 / spq)
    by_onset = {round(q, 4): ids for q, ids in score.onset_note_ids()}
    lit: list[str] = []
    t = first_q
    while t < last_q - 1e-6:
        if abs(t - round(t)) < 1e-6 and counts is not None:
            counts[int(round(t))].set_color(HIGHLIGHT)
        ids = by_onset.get(round(t, 4))
        if ids:
            for i in lit:
                score.note(i).set_color(INK)
            for i in ids:
                score.note(i).set_color(HIGHLIGHT)
            lit = ids
        scene.wait(spq / 2)
        t += 0.5
        if abs(t - round(t)) < 1e-6 and counts is not None and int(round(t)) - 1 < len(counts):
            counts[int(round(t)) - 1].set_color(base_colors[int(round(t)) - 1])
    for i in lit:
        score.note(i).set_color(INK)


def _italic(text: str, size: float = 40, color=BLUE) -> Text:
    """Tempo marks are printed in italics."""
    return Text(text, font=FONT, font_size=size, color=color, slant=ITALIC)


def _timesig(top: str, bottom: str, ss: float = 0.42) -> VGroup:
    """A free-standing time signature from SMuFL digits (centred stack)."""
    def number(digits: str) -> VGroup:
        glyphs = VGroup(*(SmuflGlyph(f"timeSig{d}", staff_space=ss) for d in digits))
        return glyphs.arrange(RIGHT, buff=0.02)

    upper, lower = number(top), number(bottom)
    upper.move_to(UP * ss)
    lower.move_to(DOWN * ss)
    return VGroup(upper, lower)


def _set_time_symbol(xml: str, symbol: str) -> str:
    """Print the time signature as a sign: 'common' (C) or 'cut' (C|)."""
    return xml.replace("<time>", f'<time symbol="{symbol}">', 1)


# -- lessons --------------------------------------------------------------------

class RhythmMeasureTempo(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a two-measure tune, played
        self.title()
        xml = snippet("3/4 c'4 e'8 d' c'4 g2.")
        score = engraved(xml, width=11.0, max_height=6.0, y=1.0)
        notes = [(0, "C5", 1), (1, "E5", 0.5), (1.5, "D5", 0.5), (2, "C5", 1), (3, "G4", 3)]
        spq = 0.6
        labels = VGroup(*(words(self.t(k), 44, MUTED, weight="BOLD") for k in ("label-rhythm", "label-measure", "label-tempo")))
        for label, x in zip(labels, (-4.2, 0.0, 4.2)):
            label.move_to(np.array([x, -1.7, 0.0]))
        self.play(FadeIn(score), run_time=0.5)
        self.caption("time", wait=False)
        lit_play(self, score, [(s * spq, (p,), d * spq * 0.95) for s, p, d in notes], spq)
        self.play(FadeIn(labels), run_time=0.5)
        self.wait(0.8)

        # {[2]} Checkpoint: rhythm — the long and short, tapped on one note
        self.caption("rhythm", wait=False)
        self.play(labels[0].animate.set_color(HIGHLIGHT), run_time=0.3)
        lit_play(self, score, [(s * spq, ("G4",), d * spq * 0.9) for s, _, d in notes], spq)
        self.wait(1.2)
        self.play(labels[0].animate.set_color(INK), run_time=0.3)

        # {[3]} Checkpoint: measure — beats grouped by bar lines, counted 1 2 3
        bottom, top = _content_box(score)
        xs = _beat_xs(score, 6, end_q=6)
        counts = _counts(xs, bottom - 0.45, 3, colors=lambda n: INK if n == 1 else MUTED, size=40)
        base = [c.get_color() for c in counts]
        self.caption("measure", wait=False)
        self.play(labels[1].animate.set_color(HIGHLIGHT), FadeIn(counts), run_time=0.4)
        for _ in range(2):
            _walk(self, score, counts, base, notes, 0, 6, spq, lambda s, d: STRONG if s % 3 == 0 else WEAK)
        self.wait(1.0)
        self.play(labels[1].animate.set_color(INK), FadeOut(counts), run_time=0.3)

        # {[4]} Checkpoint: tempo — the same music, faster
        self.caption("tempo", wait=False)
        self.play(labels[2].animate.set_color(HIGHLIGHT), run_time=0.3)
        quarter = SmuflGlyph("metNoteQuarterUp", staff_space=0.32)
        for bpm in (100, 176):
            fast = 60 / bpm
            mark = VGroup(quarter.copy(), words(f"= {bpm}", 36, INK)).arrange(RIGHT, buff=0.15)
            mark.move_to(np.array([0.0, bottom - 0.5, 0.0]))
            self.play(FadeIn(mark), run_time=0.3)
            for _ in range(2):
                lit_play(self, score, [(s * fast, (p,), d * fast * 0.95) for s, p, d in notes], fast, tail=0.25)
            self.play(FadeOut(mark), run_time=0.3)
        self.wait(1.0)

        # {[5]} Checkpoint: remember
        self.remember()


class StrongBeatsAndSyncopation(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; two measures with every beat counted
        self.title()
        xml = snippet("4/4 c'2 e'4 g' e' g'2 c'4")
        score = engraved(xml, width=11.0, max_height=6.0, y=0.85)
        notes = [(0, "C5", 2), (2, "E5", 1), (3, "G5", 1), (4, "E5", 1), (5, "G5", 2), (7, "C5", 1)]
        bottom, top = _content_box(score)
        counts = _counts(_beat_xs(score, 8, end_q=8), bottom - 0.45, 4, size=44)
        base = [MUTED] * 8
        self.play(FadeIn(score), FadeIn(counts), run_time=0.5)
        spq = 0.6

        def regular(s, d):
            return STRONG if s % 4 == 0 else (MEDIUM if s % 4 == 2 else WEAK)

        # {[2]} Checkpoint: beat 1 is the strongest
        for b in (0, 4):
            base[b] = HIGHLIGHT
        self.caption("strong", wait=False)
        self.play(*(counts[b].animate.set_color(HIGHLIGHT).scale(1.2) for b in (0, 4)), run_time=0.4)
        _walk(self, score, counts, base, notes, 0, 4, spq, regular)
        _walk(self, score, counts, base, notes, 0, 4, spq, regular)
        self.wait(1.0)

        # {[3]} Checkpoint: in four, beat 3 is strong too
        for b in (2, 6):
            base[b] = BLUE
        self.caption("four", wait=False)
        self.play(*(counts[b].animate.set_color(BLUE).scale(1.1) for b in (2, 6)), run_time=0.4)
        _walk(self, score, counts, base, notes, 0, 4, spq, regular)
        self.wait(2.0)

        # {[4]} Checkpoint: syncopation — the accent on beat 2
        accent = SmuflGlyph("articAccentAbove", staff_space=0.4, color=RED)
        long_note = score.onset_note_ids()[4][1][0]  # the half note on beat 2 of measure 2
        accent.move_to(np.array([_head_x(score, long_note), max(top, _note_top(score, long_note)) + 0.35, 0.0]))
        self.caption("syncopation", wait=False)
        self.play(FadeIn(accent, shift=DOWN * 0.2), counts[5].animate.set_color(RED).scale(1.25), run_time=0.5)
        base[5] = RED

        def syncopated(s, d):
            return 122 if s == 5 else (WEAK if s % 4 else MEDIUM)

        for _ in range(2):
            _walk(self, score, counts, base, notes, 4, 8, spq, syncopated)
        self.wait(1.2)

        # {[5]} Checkpoint: both measures — regular, then syncopated
        self.caption("here", wait=False)
        for _ in range(2):
            _walk(self, score, counts, base, notes, 0, 8, spq, lambda s, d: syncopated(s, d) if 4 <= s < 8 else regular(s, d))
        self.wait(1.5)

        # {[6]} Checkpoint: remember
        self.remember()


class SimpleAndCompound(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; a simple and a compound tune
        self.title()
        specs = (
            ("2/4 c'8 d' e' f' g'4 e'", [(0, "C5", .5), (.5, "D5", .5), (1, "E5", .5), (1.5, "F5", .5), (2, "G5", 1), (3, "E5", 1)], 1.0, 2, 0.6, "label-simple", 1.7),
            ("6/8 c'8 d' e' f' e' d' c'4. g4.", [(0, "C5", .5), (.5, "D5", .5), (1, "E5", .5), (1.5, "F5", .5), (2, "E5", .5), (2.5, "D5", .5), (3, "C5", 1.5), (4.5, "G4", 1.5)], 1.5, 3, 0.4, "label-compound", -0.85),
        )
        rows = []
        for spec, notes, beat_q, split, spq, label_key, y in specs:
            score = engraved(snippet(spec), width=9.0, max_height=12.0, y=y, x=0.9)
            bottom, top = _content_box(score)
            label = words(self.t(label_key), 40, INK, weight="BOLD").move_to(np.array([-5.2, y, 0.0]))
            marks = VGroup()
            onsets = sorted(_onset_x(score).items())
            beat = 0
            for q, x in onsets:
                if abs(q / beat_q - round(q / beat_q)) < 1e-6:
                    marks.add(words(str(beat % 2 + 1), 36, HIGHLIGHT).move_to(np.array([x, bottom - 0.32, 0.0])))
                    beat += 1
                else:
                    marks.add(Dot(radius=0.07, fill_color=MUTED).move_to(np.array([x, bottom - 0.32, 0.0])))
            # (the beams already group the eighths by beat: two, or three)
            rows.append((score, notes, beat_q, split, spq, label, marks, VGroup()))
            self.play(FadeIn(score), FadeIn(label), run_time=0.5)

        def play(row):
            score, notes, beat_q, _, spq, *_ = row
            events = [(s, (p,), d * 0.95, STRONG if abs(s / beat_q - round(s / beat_q)) < 1e-6 else WEAK) for s, p, d in notes]
            _accented_sound(self, events, qpm=60 / spq)
            lit = []
            clock = 0.0
            for q, ids in score.onset_note_ids():
                if q * spq > clock:
                    self.wait(q * spq - clock)
                    clock = q * spq
                for i in lit:
                    score.note(i).set_color(INK)
                for i in ids:
                    score.note(i).set_color(HIGHLIGHT)
                lit = ids
            last = max(s + d for s, _, d in notes) * spq
            self.wait(last - clock + 0.3)
            for i in lit:
                score.note(i).set_color(INK)

        def introduce(key, row):
            self.caption(key, wait=False)
            self.play(FadeIn(row[6]), FadeIn(row[7]), row[5].animate.set_color(HIGHLIGHT), run_time=0.5)
            play(row)
            play(row)
            self.wait(1.5)
            self.play(row[5].animate.set_color(INK), run_time=0.3)

        # {[2]} Checkpoint: simple — two beats, each split in two
        introduce("simple", rows[0])

        # {[3]} Checkpoint: compound — two beats, each split in three
        introduce("compound", rows[1])

        # {[4]} Checkpoint: hear them back to back
        self.caption("hear", wait=False)
        for row in rows:
            row[5].set_color(HIGHLIGHT)
            play(row)
            row[5].set_color(INK)
            self.wait(0.4)
        self.wait(1.0)
        self.clear_stage()

        # {[5]} Checkpoint: the table — two, three, four beats of each kind
        heads = VGroup(*(words(self.t(f"beats-{n}"), 34, MUTED) for n in (2, 3, 4)))
        columns = (-1.4, 1.7, 4.8)
        for head, x in zip(heads, columns):
            head.move_to(np.array([x, 2.3, 0.0]))
        table = VGroup(heads)
        for (label_key, sigs), y in ((("label-simple", (("2", "4"), ("3", "4"), ("4", "4"))), 1.0), (("label-compound", (("6", "8"), ("9", "8"), ("12", "8"))), -1.15)):
            row = VGroup(words(self.t(label_key), 40, INK, weight="BOLD").move_to(np.array([-4.8, y, 0.0])))
            for (top_, bottom_), x in zip(sigs, columns):
                row.add(_timesig(top_, bottom_).move_to(np.array([x, y, 0.0])))
            table.add(row)
        self.caption("table", wait=False)
        self.play(FadeIn(heads), run_time=0.4)
        for row in table[1:]:
            self.play(FadeIn(row, shift=RIGHT * 0.2), run_time=0.5)
        self.wait(reading_time(self.t("table")) + 1.0)

        # {[6]} Checkpoint: remember
        self.remember()


class CommonAndCutTime(LessonScene):
    def construct(self):
        # {[1]} Checkpoint: title; the C sign on a staff, and what it means
        self.title()
        ss = 0.55
        left = Staff(width_ss=8.0, staff_space=ss).move_to(np.array([-3.0, 0.5, 0.0]))
        right = Staff(width_ss=8.0, staff_space=ss).move_to(np.array([3.0, 0.5, 0.0]))
        clefs = VGroup(left.clef("gClef", x_ss=0.6), right.clef("gClef", x_ss=0.6))
        common = left.place(SmuflGlyph("timeSigCommon", staff_space=ss), 4.6, 4)
        four_four = VGroup(
            right.place(SmuflGlyph("timeSig4", staff_space=ss), 4.6, 6),
            right.place(SmuflGlyph("timeSig4", staff_space=ss), 4.6, 2),
        )
        equals = words("=", 60, MUTED).move_to(np.array([0.0, 0.5, 0.0]))
        self.play(FadeIn(left), FadeIn(clefs[0]), FadeIn(common), run_time=0.5)
        self.caption("common", wait=False)
        self.play(common.animate.set_color(HIGHLIGHT), run_time=0.3)
        self.play(FadeIn(equals), FadeIn(right), FadeIn(clefs[1]), FadeIn(four_four), run_time=0.6)
        self.wait(reading_time(self.t("common")))
        self.clear_stage()

        # {[2]} Checkpoint: counted in four
        notes = [(0, "C5", 1), (1, "E5", 1), (2, "D5", 1), (3, "F5", 1), (4, "E5", 2), (6, "C5", 2)]
        xml4 = _set_time_symbol(snippet("4/4 c'4 e' d' f' e'2 c'2"), "common")
        score = engraved(xml4, width=11.0, max_height=6.0, y=0.9)
        bottom, _ = _content_box(score)
        counts = _counts(_beat_xs(score, 8, end_q=8), bottom - 0.45, 4, colors=lambda n: INK if n == 1 else MUTED, size=40)
        base = [c.get_color() for c in counts]
        self.play(FadeIn(score), FadeIn(counts), run_time=0.5)
        self.caption("count-four", wait=False)
        for _ in range(2):
            _walk(self, score, counts, base, notes, 0, 8, 0.55, lambda s, d: STRONG if s % 4 == 0 else (MEDIUM if s % 4 == 2 else WEAK))
        self.wait(0.6)

        # {[3]} Checkpoint: cut time — the same notes, two half-note beats
        xml2 = _set_time_symbol(snippet("2/2 c'4 e' d' f' e'2 c'2"), "cut")
        cut = engraved(xml2, width=11.0, max_height=6.0, y=0.9)
        b2, _ = _content_box(cut)
        half_xs = _beat_xs(cut, 4, beat_q=2.0, end_q=8)
        cut_counts = _counts(half_xs, b2 - 0.45, 2, colors=lambda n: INK if n == 1 else MUTED, size=40)
        self.caption("cut", wait=False)
        self.play(FadeOut(score), FadeOut(counts), FadeIn(cut), FadeIn(cut_counts), run_time=0.6)
        self.wait(reading_time(self.t("cut")))

        # {[4]} Checkpoint: counted in two — lighter, quicker
        self.caption("count-two", wait=False)
        spq = 0.32
        by_onset = {round(q, 4): ids for q, ids in cut.onset_note_ids()}
        for _ in range(2):
            events = [(s, (p,), d * 0.95, STRONG if s % 4 == 0 else (MEDIUM if s % 2 == 0 else WEAK)) for s, p, d in notes]
            events += [(b, (TICK,), 0.1, 34) for b in range(0, 8, 2)]
            _accented_sound(self, events, qpm=60 / spq)
            lit: list[str] = []
            for q in range(8):
                if q % 2 == 0:
                    cut_counts[q // 2].set_color(HIGHLIGHT)
                ids = by_onset.get(float(q)) or by_onset.get(q)
                if ids:
                    for i in lit:
                        cut.note(i).set_color(INK)
                    for i in ids:
                        cut.note(i).set_color(HIGHLIGHT)
                    lit = ids
                self.wait(spq)
                if q % 2 == 1:
                    cut_counts[q // 2].set_color(INK if (q // 2) % 2 == 0 else MUTED)
            for i in lit:
                cut.note(i).set_color(INK)
            self.wait(0.3)
        self.wait(1.2)
        self.clear_stage()

        # {[5]} Checkpoint: not a letter — a broken circle
        sign = SmuflGlyph("timeSigCommon", staff_space=1.4).move_to(np.array([0.0, 0.6, 0.0]))
        self.caption("circle", wait=False)
        self.play(FadeIn(sign, scale=1.2), run_time=0.5)
        self.play(sign.animate.set_color(HIGHLIGHT), run_time=0.4)
        self.wait(reading_time(self.t("circle")))

        # {[6]} Checkpoint: the medieval signs — full circle three, broken circle two
        circle = SmuflGlyph("mensuralProlation2", staff_space=1.3).move_to(np.array([-2.6, 0.7, 0.0]))
        broken = SmuflGlyph("mensuralProlation6", staff_space=1.3).move_to(np.array([2.6, 0.7, 0.0]))
        circle_label = words(self.t("label-three"), 40, INK).next_to(circle, DOWN, buff=0.5)
        broken_label = words(self.t("label-two"), 40, INK).next_to(broken, DOWN, buff=0.5)
        self.caption("old", wait=False)
        self.play(FadeOut(sign), FadeIn(circle), FadeIn(broken), FadeIn(circle_label), FadeIn(broken_label), run_time=0.6)
        self.play(broken.animate.set_color(HIGHLIGHT), broken_label.animate.set_color(HIGHLIGHT), run_time=0.3)
        self.wait(reading_time(self.t("old")) + 0.5)

        # {[7]} Checkpoint: remember
        self.remember()


class TempoWords(LessonScene):
    LADDER = ("grave", "largo", "larghetto", "andante", "moderato", "allegro", "vivace", "presto")

    def construct(self):
        # {[1]} Checkpoint: title; the Italian words, slow to fast, as a staircase
        self.title()
        rungs = VGroup()
        for i, key in enumerate(self.LADDER):
            word = _italic(self.t(f"word-{key}"), 40, INK)
            word.move_to(np.array([-5.0 + i * 1.45, -1.55 + i * 0.5, 0.0]), aligned_edge=LEFT)
            rungs.add(word)
        if rungs.get_right()[0] > 6.6:
            rungs.shift(LEFT * (rungs.get_right()[0] - 6.6))
        self.caption("italian", wait=False)
        for word in rungs:
            self.play(FadeIn(word, shift=UP * 0.15), run_time=0.3)
        self.wait(max(reading_time(self.t("italian")) - 2.4, 0.0) + 1.0)

        # {[2]} Checkpoint: the words become a row; a tune to play at four tempi
        row = VGroup(*(_italic(self.t(f"word-{key}"), 30, MUTED) for key in self.LADDER)).arrange(RIGHT, buff=0.38)
        if row.get_width() > 13.2:
            row.set_width(13.2)
        row.move_to(np.array([0.0, 2.3, 0.0]))
        self.play(Transform(rungs, row), run_time=0.8)
        xml = snippet("4/4 c'4 e'8 d' c'4 g a8 b c' d' c'2")
        score = engraved(xml, width=10.0, max_height=6.0, y=0.55)
        notes = [(0, "C5", 1), (1, "E5", .5), (1.5, "D5", .5), (2, "C5", 1), (3, "G4", 1),
                 (4, "A4", .5), (4.5, "B4", .5), (5, "C5", .5), (5.5, "D5", .5), (6, "C5", 2)]
        self.play(FadeIn(score), run_time=0.5)
        bottom, _ = _content_box(score)

        # {[3]} Checkpoint: largo, andante, allegro, presto
        self.caption("play", wait=False)
        quarter = SmuflGlyph("metNoteQuarterUp", staff_space=0.34)
        for key, bpm in (("largo", 54), ("andante", 80), ("allegro", 132), ("presto", 184)):
            i = self.LADDER.index(key)
            spq = 60 / bpm
            mark = VGroup(quarter.copy(), words(f"= {bpm}", 36, INK)).arrange(RIGHT, buff=0.15)
            mark.move_to(np.array([0.0, bottom - 0.5, 0.0]))
            self.play(rungs[i].animate.set_color(HIGHLIGHT).scale(1.25), FadeIn(mark), run_time=0.3)
            lit_play(self, score, [(s * spq, (p,), d * spq * 0.95) for s, p, d in notes], spq, tail=0.3)
            self.play(rungs[i].animate.set_color(MUTED).scale(1 / 1.25), FadeOut(mark), run_time=0.3)

        # {[4]} Checkpoint: the words carry a mood too
        self.caption("mood", wait=False)
        for key in ("andante", "allegro"):
            self.play(rungs[self.LADDER.index(key)].animate.set_color(BLUE).scale(1.25), run_time=0.4)
        self.wait(reading_time(self.t("mood")))
        self.clear_stage()

        # {[5]} Checkpoint: the metronome mark — exact beats per minute
        mm = words(self.t("mm"), 64, INK, weight="BOLD").move_to(np.array([-1.0, 0.7, 0.0]))
        pulse = Dot(radius=0.32, fill_color=HIGHLIGHT).next_to(mm, RIGHT, buff=0.8)
        self.play(FadeIn(mm), run_time=0.4)
        self.caption("metronome", wait=False)
        beat = 60 / 92
        add_events_sound(self, [(i * beat, (TICK,), 0.08) for i in range(8)])
        for _ in range(8):
            self.add(pulse)
            self.wait(beat * 0.4)
            self.remove(pulse)
            self.wait(beat * 0.6)
        self.wait(1.0)

        # {[6]} Checkpoint: remember
        self.remember()


class ChangingTempo(LessonScene):
    PITCHES = ["G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5"]

    def construct(self):
        # {[1]} Checkpoint: title; a scale to play, and a time strip beneath it
        self.title()
        row = NoteRow(self.PITCHES, staff_space=0.42, spacing_ss=3.0)
        row.move_to(np.array([0.0, 0.55, 0.0]))
        x0, x1, strip_y, span = -6.2, 6.2, -1.55, 6.6  # strip: `span` seconds wide
        strip = Line(np.array([x0, strip_y, 0]), np.array([x1, strip_y, 0])).set_stroke(MUTED, width=3)
        self.play(FadeIn(row), FadeIn(strip), run_time=0.5)
        state = {"dots": VGroup(), "words": VGroup()}

        def x_at(t):
            return x0 + (x1 - x0) * t / span

        def demo(durations, marks=(), end_marker=False):
            """Play the scale with these note lengths (seconds), drop a dot on
            the strip at each onset, and print tempo words at their notes."""
            self.play(FadeOut(state["dots"]), FadeOut(state["words"]), run_time=0.3)
            dots, labels = VGroup(), VGroup()
            for index, key in marks:
                label = _italic(self.t(key), 38, BLUE)
                label.move_to(np.array([row.note_x(index), row.staff.get_top()[1] + 0.85, 0.0]), aligned_edge=LEFT)
                labels.add(label)
            if labels:
                self.play(FadeIn(labels), run_time=0.3)
            onsets = np.concatenate([[0.0], np.cumsum(durations)[:-1]])
            add_events_sound(self, [(t, (p,), d * 0.92) for t, p, d in zip(onsets, self.PITCHES, durations)])
            for i, (t, d) in enumerate(zip(onsets, durations)):
                dot = Dot(radius=0.11, fill_color=HIGHLIGHT).move_to(np.array([x_at(t), strip_y, 0.0]))
                dots.add(dot)
                self.add(dot)
                row.notes[i].set_color(HIGHLIGHT)
                self.wait(d)
                row.notes[i].set_color(INK)
                dot.set_fill(INK)
            if end_marker:
                total = float(np.sum(durations))
                dots.add(Line(np.array([x_at(total), strip_y + 0.35, 0]), np.array([x_at(total), strip_y - 0.35, 0])).set_stroke(BLUE, width=4))
                self.add(dots[-1])
            state["dots"], state["words"] = dots, labels

        # {[2]} Checkpoint: a steady tempo — even dots
        self.caption("steady", wait=False)
        demo([0.5] * 8, end_marker=True)
        self.wait(1.0)

        # {[3]} Checkpoint: ritardando — the gaps grow
        self.caption("rit", wait=False)
        demo([0.5, 0.5, 0.5, 0.56, 0.66, 0.8, 0.98, 1.2], marks=[(2, "word-rit")])
        self.wait(0.8)

        # {[4]} Checkpoint: a tempo — back to the first speed
        self.caption("a-tempo", wait=False)
        demo([0.5, 0.5, 0.62, 0.78, 0.98, 0.5, 0.5, 0.5], marks=[(1, "word-rit"), (5, "word-a-tempo")])
        self.wait(0.8)

        # {[5]} Checkpoint: accelerando — the gaps shrink
        self.caption("accel", wait=False)
        demo([0.9, 0.78, 0.67, 0.58, 0.5, 0.43, 0.37, 0.32], marks=[(0, "word-accel")])
        self.wait(0.8)

        # {[6]} Checkpoint: meno mosso and più mosso — the change at once
        self.caption("meno", wait=False)
        demo([0.45] * 4 + [0.8] * 4, marks=[(4, "word-meno")])
        self.wait(0.6)
        demo([0.75] * 4 + [0.36] * 4, marks=[(4, "word-piu")])
        self.wait(0.8)

        # {[7]} Checkpoint: rubato — uneven, but the same total
        self.caption("rubato", wait=False)
        demo([0.4, 0.48, 0.6, 0.72, 0.52, 0.42, 0.38, 0.48], marks=[(0, "word-rubato")], end_marker=True)
        self.wait(1.2)

        # {[8]} Checkpoint: remember
        self.remember()

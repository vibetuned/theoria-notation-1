"""Module 05 lessons (Gehrkens chs. IV, V, XIII): the signs that say how
to play — ties and slurs, dots, articulation, dynamics, the road map of
repeats and jumps, the fermata, and the octave signs.

One idea per video; every word on screen comes from content/<lang>/.
Ties/slurs and articulation are engraved by Verovio (Tier 2, MusicXML
decorated here with lxml); the dynamics and road-map videos draw Tier 1
staves (`_Bars`) so measure boxes, brackets and marks sit at known
places. Playback goes through a local velocity-aware renderer
(`_sound`): staccato is really short, accents and dynamics are really
louder or softer.

Render (from the repo root):
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/05-signs-and-expression/scenes.py TiesAndSlurs -w -l
"""

from __future__ import annotations

import hashlib
import re
import subprocess

import mido
import numpy as np
from lxml import etree
from manimlib import (
    DOWN,
    ITALIC,
    LEFT,
    PI,
    RIGHT,
    UP,
    CurvedArrow,
    DashedLine,
    FadeIn,
    FadeOut,
    GrowFromPoint,
    Line,
    Rectangle,
    RoundedRectangle,
    ShowCreation,
    Text,
    VGroup,
)

from theoria.core.examples import snippet
from theoria.core.pitches import diatonic_steps_from
from theoria.notation import engrave
from theoria.notation.glyphs import Notehead, SmuflGlyph, stem_for
from theoria.notation.lesson import LABEL_SIZE, SMALL_SIZE, LessonScene, reading_time, words
from theoria.notation.score import _Fragment
from theoria.notation.staff import STAFF_REFERENCE, Staff
from theoria.paths import DEFAULT_SOUNDFONT, MEDIA_DIR
from theoria.theme import BLUE, FONT, HIGHLIGHT, INK, MUTED, ORANGE

# ---------------------------------------------------------------------------
# Sound with velocities (kit candidate). theoria.audio has no dynamics, and
# this module is ABOUT dynamics: events here are (start s, pitches, length
# s, velocity). "click" is a wood block on the drum channel (a soft beat).

_PITCH_CLASS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_TICKS = 960


def _midi(name: str) -> int:
    middle = name[1:-1]
    return 12 * (int(name[-1]) + 1) + _PITCH_CLASS[name[0]] + middle.count("#") - middle.count("-")


def _sound(scene, events, gain: float = 0.8) -> None:
    """Queue `events` at the scene's current time (mido -> FluidSynth, cached)."""
    events = [(round(s, 4), tuple(p), round(d, 4), int(v)) for s, p, d, v in events]
    digest = hashlib.md5(repr(("velocity-v1", events, gain)).encode()).hexdigest()[:16]
    wav = MEDIA_DIR / "audio" / f"vel-{digest}.wav"
    if not wav.exists():
        wav.parent.mkdir(parents=True, exist_ok=True)
        timeline = []
        for start, pitches, seconds, velocity in events:
            for pitch in pitches:
                channel, note = (9, 76) if pitch == "click" else (0, _midi(pitch))
                on, off = round(start * _TICKS), round((start + seconds) * _TICKS)
                timeline.append((on, 1, mido.Message("note_on", channel=channel, note=note, velocity=velocity)))
                timeline.append((off, 0, mido.Message("note_off", channel=channel, note=note, velocity=0)))
        timeline.sort(key=lambda item: (item[0], item[1]))
        midi = mido.MidiFile(ticks_per_beat=_TICKS)
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=1_000_000))  # one beat = one second
        track.append(mido.Message("program_change", channel=0, program=0))
        now = 0
        for tick, _, message in timeline:
            track.append(message.copy(time=tick - now))
            now = tick
        mid_path = wav.with_suffix(".mid")
        midi.save(str(mid_path))
        subprocess.run(
            ["fluidsynth", "-ni", "-g", str(gain), "-r", "44100", "-F", str(wav), str(DEFAULT_SOUNDFONT), str(mid_path)],
            check=True,
            capture_output=True,
        )
    scene.add_sound(str(wav))


def _perform(scene, events, cues, actions=(), tail: float = 0.5, color=HIGHLIGHT, rest=INK):
    """Sound `events` and, in sync, light each cue's mobjects from its time
    to the next cue; `actions` are (time, callable) run at their time."""
    _sound(scene, events)
    timeline = [(t, 0, mobs) for t, mobs in cues] + [(t, 1, fn) for t, fn in actions]
    timeline.sort(key=lambda item: (item[0], item[1]))
    clock, lit = 0.0, []
    for t, kind, payload in timeline:
        if t > clock + 1e-3:
            scene.wait(t - clock)
            clock = t
        if kind == 1:
            payload()
            continue
        for mob in lit:
            mob.set_color(rest)
        for mob in payload:
            mob.set_color(color)
        lit = list(payload)
    end = max(s + d for s, _, d, _ in events)
    scene.wait(max(end - clock, 0.0) + tail)
    for mob in lit:
        mob.set_color(rest)


def _italic(text: str, size: float = LABEL_SIZE, color=INK, weight: str = "NORMAL") -> Text:
    """Score words (Fine, cresc., loco...) are italic, as printed."""
    return Text(text, font=FONT, font_size=size, color=color, slant=ITALIC, weight=weight).set_color(color)


def _bold(text: str, size: float = LABEL_SIZE, color=INK) -> Text:
    """Bold label. (kit bug: words(..., weight="BOLD") drops its colour —
    Pango bold markup wins — so the colour is set again afterwards.)"""
    return words(text, size, color, weight="BOLD").set_color(color)


class _Lesson(LessonScene):
    """Captions that run while music plays, then hold for what is left of
    their reading time."""

    def say(self, key: str, color=INK):
        self.caption(key, wait=False, color=color)
        self._said = (self.time, reading_time(self.t(key)))

    def settle(self, extra: float = 0.4):
        start, need = self._said
        self.wait(max(need - (self.time - start), 0.0) + extra)


# ---------------------------------------------------------------------------
# Tier 2: tinyNotation snippets, decorated with lxml, engraved by Verovio,
# with the geometry (staff lines, heads, measures) mapped to the scene.

_DURATION = {"1": 4.0, "2": 2.0, "4": 1.0, "8": 0.5, "16": 0.25, "32": 0.125}


def _beats(duration: str) -> float:
    base = duration.rstrip(".")
    dots = len(duration) - len(base)
    return _DURATION[base] * (2 - 0.5**dots)


def _tiny(time: str, tokens: list[str]) -> str:
    """'G4:2~' tokens -> tinyNotation ('g2~'); c = C4, c' = C5, C = C3."""
    parts = [time]
    for token in tokens:
        pitch, duration = token.split(":")
        if pitch == "r":
            parts.append(f"r{duration}")
            continue
        letter, middle, octave = pitch[0], pitch[1:-1], int(pitch[-1])
        name = letter.lower() + middle + "'" * (octave - 4) if octave >= 4 else letter.upper() * (4 - octave) + middle
        parts.append(name + duration)
    return " ".join(parts)


def _events(tokens, spb: float, start: float = 0.0, velocity: int = 72, length: float = 0.92, per=None):
    """(events, cues, end) for a token list; ties merge into one sound,
    lighting every note of the tie. `per`: note index -> {velocity, length}."""
    per = per or {}
    events, cues = [], []
    t, index, pending = start, 0, None
    for token in tokens:
        pitch, duration = token.split(":")
        tie = duration.endswith("~")
        beats = _beats(duration.rstrip("~"))
        if pitch == "r":
            t += beats * spb
            continue
        if pending is None:
            options = per.get(index, {})
            pending = [t, pitch, beats, [index], options.get("velocity", velocity), options.get("length", length)]
        else:
            pending[2] += beats
            pending[3].append(index)
        t += beats * spb
        index += 1
        if not tie:
            t0, p, b, indices, v, fraction = pending
            events.append((t0, (p,), b * spb * fraction, v))
            cues.append((t0, indices))
            pending = None
    return events, cues, t


def _decorate(xml: str, marks=None, slurs=()) -> str:
    """Add articulation / fermata marks ({note index: [names]}) and slurs
    ([(first, last)]) to snippet MusicXML. Indices count notes, not rests."""
    root = etree.fromstring(xml.encode())
    notes = [n for n in root.iter("note") if n.find("rest") is None]

    def notations(note):
        found = note.find("notations")
        return found if found is not None else etree.SubElement(note, "notations")

    for index, names in (marks or {}).items():
        for name in names:
            holder = notations(notes[index])
            if name == "fermata":
                etree.SubElement(holder, "fermata").set("type", "upright")
                continue
            group = holder.find("articulations")
            if group is None:
                group = etree.SubElement(holder, "articulations")
            mark = etree.SubElement(group, name)
            if name == "strong-accent":
                mark.set("type", "up")
    for number, (first, last) in enumerate(slurs, start=1):
        for index, kind in ((first, "start"), (last, "stop")):
            slur = etree.SubElement(notations(notes[index]), "slur")
            slur.set("type", kind)
            slur.set("number", str(number))
    return etree.tostring(root, encoding="unicode")


_SVG = "{http://www.w3.org/2000/svg}"
_XLINK = "{http://www.w3.org/1999/xlink}href"
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


class _Engraved(VGroup):
    """A Verovio-engraved snippet that knows where its staff lines, note
    heads, measures and bar lines are in scene coordinates (kit candidate;
    parsed from the SVG itself, page-margin translate included).
    Sized by STAFF SPACE (`staff_space`, shrunk to fit `max_width`), and
    centred on its staff, not on the page canvas."""

    def __init__(self, xml: str, staff_space: float = 0.42, max_width: float = 12.4, center=(0.0, 0.5), spacing=None):
        super().__init__()
        options = {} if spacing is None else {"spacingLinear": spacing[0], "spacingNonLinear": spacing[1]}
        raw, _ = engrave.render_svg(xml, options)
        svg = engrave.preprocess(raw, INK)
        self.ids = engrave.note_ids(svg)
        self.background = _Fragment(engrave.without_notes(svg))
        self.fragments = {i: _Fragment(engrave.isolate(svg, i)) for i in self.ids}
        self.add(self.background, *self.fragments.values())
        self._parse(raw)
        width_ss = (self.staff_x[1] - self.staff_x[0]) / self.unit
        self.ss = min(staff_space, max_width / width_ss)
        self.set_width(self.view[2] * self.ss / self.unit)
        middle = self.point((self.staff_x[0] + self.staff_x[1]) / 2, (self.lines[0] + self.lines[-1]) / 2)
        self.shift(np.array([center[0], center[1], 0.0]) - middle)

    def _parse(self, raw: str):
        root = etree.fromstring(raw.encode())
        inner = next(el for el in root.iter(f"{_SVG}svg") if el.get("class") == "definition-scale")
        self.view = [float(v) for v in inner.get("viewBox").split()]
        lines, xs = set(), []
        self.heads, self.measures, self.barlines = {}, [], []

        def walk(el, dx, dy):
            transform = el.get("transform") or ""
            if el.tag == f"{_SVG}g" and transform.startswith("translate"):
                a, b = (float(v) for v in _NUMBER.findall(transform)[:2])
                dx, dy = dx + a, dy + b
            kind = el.get("class") or ""
            if kind == "measure":
                self.measures.append([])
            elif kind == "staff":
                for path in el.findall(f"{_SVG}path"):
                    x0, y0, x1, _ = (float(v) for v in _NUMBER.findall(path.get("d")))
                    lines.add(round(y0 + dy, 1))
                    xs.extend([x0 + dx, x1 + dx])
                    if self.measures:
                        self.measures[-1].extend([x0 + dx, x1 + dx])
            elif kind == "barLine":
                bx = [float(_NUMBER.findall(p.get("d"))[0]) + dx for p in el.findall(f"{_SVG}path")]
                if bx:
                    self.barlines.append((min(bx), max(bx)))
            elif kind.split()[:1] == ["note"] and el.get("id"):
                use = el.find(f".//{_SVG}g[@class='notehead']/{_SVG}use")
                if use is not None:
                    x, y, scale = (float(v) for v in _NUMBER.findall(use.get("transform"))[:3])
                    width = 1.688 if use.get(_XLINK, "")[1:5] == "E0A2" else 1.18
                    self.heads[el.get("id")] = (x + dx + width * 90 * scale / 0.72, y + dy)
            for child in el:
                walk(child, dx, dy)

        walk(inner, 0.0, 0.0)
        self.lines = sorted(lines)[:5]  # top line first (SVG y grows down)
        self.unit = (self.lines[-1] - self.lines[0]) / 4
        self.staff_x = (min(xs), max(xs))
        self.measures = [(min(m), max(m)) for m in self.measures if m]

    def point(self, x: float, y: float) -> np.ndarray:
        k = self.get_width() / self.view[2]
        return np.array([self.get_left()[0] + (x - self.view[0]) * k, self.get_top()[1] - (y - self.view[1]) * k, 0.0])

    def note(self, i: int):
        return self.fragments[self.ids[i]]

    def head(self, i: int) -> np.ndarray:
        return self.point(*self.heads[self.ids[i]])

    def top(self) -> float:
        return self.point(0, self.lines[0])[1]

    def bottom(self) -> float:
        return self.point(0, self.lines[-1])[1]

    def measure_span(self, m: int) -> tuple[float, float]:
        x0, x1 = self.measures[m]
        return self.point(x0, 0)[0], self.point(x1, 0)[0]

    def barline_x(self, k: int) -> float:
        return self.point(sum(self.barlines[k]) / 2, 0)[0]

    def staff_left(self) -> np.ndarray:
        return self.point(self.staff_x[0], (self.lines[0] + self.lines[-1]) / 2)


# ---------------------------------------------------------------------------
# Tier 1: a staff of a few measures at known positions (kit candidate).

_HEAD_WIDTH = {"whole": 1.688, "half": 1.18, "quarter": 1.18}
_KIND_BEATS = {"whole": 4.0, "half": 2.0, "quarter": 1.0}
_BAR_GLYPH = {"single": "barlineSingle", "double": "barlineDouble", "final": "barlineFinal", "repeat": "repeatRight"}
_BAR_WIDTH = {"single": 0.144, "double": 0.576, "final": 0.912, "repeat": 1.468}


class _Bars(VGroup):
    """Measures of whole/half/quarter notes ('half.' = dotted) with clef,
    optional 4/4, stems, ledger lines and chosen bar lines ('single',
    'double', 'final', 'repeat'). `gaps` {measure: staff spaces} breaks the
    staff before a measure (a coda set apart). Everything is addressable:
    notes, measure spans, staff positions."""

    def __init__(
        self,
        measures,
        ends=None,
        staff_space: float = 0.42,
        clef: str = "treble",
        time: bool = True,
        advance=None,
        gaps=None,
        center=(0.0, 0.5),
        max_width: float = 13.0,
    ):
        super().__init__()
        advance = {"whole": 4.6, "half": 3.7, "quarter": 2.8, **(advance or {})}
        ends = ends or ["single"] * (len(measures) - 1) + ["final"]
        gaps = gaps or {}
        # 1. layout in staff spaces
        left = 6.3 if time else 3.9
        self.layout, spans, breaks = [], [], []
        for m, notes in enumerate(measures):
            if m in gaps:
                breaks.append((left, left + gaps[m]))
                left += gaps[m]
            x = left + 1.3
            row = []
            for i, (pitch, kind) in enumerate(notes):
                base, dotted = kind.rstrip("."), kind.endswith(".")
                row.append((m, x, pitch, base, dotted))
                if i < len(notes) - 1:
                    x += advance[base] + (1.0 if dotted else 0.0)
            _, last_x, _, last_kind, last_dot = row[-1]
            bar = last_x + _HEAD_WIDTH[last_kind] + 1.4 + (0.9 if last_dot else 0.0)
            spans.append((left, bar + _BAR_WIDTH[ends[m]]))
            self.layout.extend(row)
            left = bar + _BAR_WIDTH[ends[m]]
        total = left
        self.ss = ss = min(staff_space, max_width / total)
        # 2. staff segments, clef, time signature
        edges = [0.0] + [v for pair in breaks for v in pair] + [total]
        self.staffs = []
        for a, b in zip(edges[::2], edges[1::2]):
            staff = Staff(width_ss=b - a, staff_space=ss)
            staff.shift(RIGHT * a * ss)
            self.staffs.append(staff)
        self.staff = self.staffs[0]
        self.reference = STAFF_REFERENCE[clef]
        self.add(*self.staffs, self.staff.clef("gClef" if clef == "treble" else "fClef", x_ss=0.8))
        if time:
            for step in (6, 2):
                glyph = SmuflGlyph("timeSig4", staff_space=ss)
                self.staff.place(glyph, 3.6, step)
                self.add(glyph)
        # 3. notes
        self.notes, self.pitches, self.beats, self.measure_of, self.steps = [], [], [], [], []
        for m, x, pitch, kind, dotted in self.layout:
            step = diatonic_steps_from(pitch, self.reference)
            head = Notehead(kind, staff_space=ss)
            self.staff.place(head, x, step)
            parts = VGroup(head, self.staff.ledger_lines(x, step, head_width_ss=_HEAD_WIDTH[kind]))
            if kind != "whole":
                direction = "up" if step < 4 else "down"
                parts.add(stem_for(head, direction, length_ss=max(3.5, abs(step - 4) / 2)))
            if dotted:
                dot = SmuflGlyph("augmentationDot", staff_space=ss)
                self.staff.place(dot, x + _HEAD_WIDTH[kind] + 0.5, step if step % 2 else step + 1)
                parts.add(dot)
            self.add(parts)
            self.notes.append(parts)
            self.pitches.append(pitch)
            self.beats.append(_KIND_BEATS[kind] * (1.5 if dotted else 1.0))
            self.measure_of.append(m)
            self.steps.append(step)
        # 4. bar lines
        self.bar_glyphs = []
        for m, style in enumerate(ends):
            glyph = SmuflGlyph(_BAR_GLYPH[style], staff_space=ss)
            self.staff.place(glyph, spans[m][1] - _BAR_WIDTH[style], 0)
            self.add(glyph)
            self.bar_glyphs.append(glyph)
        self._spans = spans
        self.total = total
        # 5. centre the staff block
        middle = self.staff.point_for(total / 2, 4)
        self.shift(np.array([center[0], center[1], 0.0]) - middle)

    def x(self, x_ss: float) -> float:
        return self.staff.point_for(x_ss, 0)[0]

    def y(self, step: float) -> float:
        return self.staff.point_for(0, step)[1]

    def span(self, m: int) -> tuple[float, float]:
        a, b = self._spans[m]
        return self.x(a), self.x(b)

    def head_x(self, i: int) -> float:
        return self.notes[i][0].get_center()[0]

    def measure_notes(self, m: int) -> list[int]:
        return [i for i, mm in enumerate(self.measure_of) if mm == m]

    def top(self) -> float:
        return self.y(8)

    def bottom(self) -> float:
        return self.y(0)

    def music_top(self) -> float:
        return max(n.get_top()[1] for n in self.notes)

    def music_bottom(self) -> float:
        return min(n.get_bottom()[1] for n in self.notes)


def _route(bars: _Bars, order, spb: float, velocity: int = 72, length: float = 0.92):
    """Play `bars` measure by measure in `order`: (events, cues, starts, end)
    where starts are (time, measure) for the tracing box."""
    events, cues, starts = [], [], []
    t = 0.0
    for m in order:
        starts.append((t, m))
        for i in bars.measure_notes(m):
            events.append((t, (bars.pitches[i],), bars.beats[i] * spb * length, velocity))
            cues.append((t, [bars.notes[i]]))
            t += bars.beats[i] * spb
    return events, cues, starts, t


def _measure_box(bars: _Bars, m: int, low: float, high: float) -> RoundedRectangle:
    x0, x1 = bars.span(m)
    box = RoundedRectangle(
        width=x1 - x0 + 0.1, height=high - low, corner_radius=0.12,
        stroke_color=HIGHLIGHT, stroke_width=4, fill_color=HIGHLIGHT, fill_opacity=0.08,
    )
    return box.move_to(np.array([(x0 + x1) / 2, (low + high) / 2, 0.0]))


# ---------------------------------------------------------------------------
# 1. Ties and slurs


class TiesAndSlurs(_Lesson):
    def construct(self):
        spb = 0.6
        untied_tokens = ["E4:4", "F4:4", "G4:2", "G4:2", "E4:2"]
        tied_tokens = ["E4:4", "F4:4", "G4:2~", "G4:2", "E4:2"]
        slur_tokens = ["G4:4", "A4:4", "B4:4", "C5:4", "D5:2", "C5:2"]
        top = (0.55, 1.4)

        # {[1]} Checkpoint: title; two G's in a row, played twice
        self.title()
        untied = _Engraved(snippet(_tiny("4/4", untied_tokens)), staff_space=0.38, max_width=11.6, center=top)
        tied = _Engraved(snippet(_tiny("4/4", tied_tokens)), staff_space=0.38, max_width=11.6, center=top)
        self.play(FadeIn(untied), run_time=0.6)
        self.say("untied")
        events, cues, _ = _events(untied_tokens, spb)
        _perform(self, events, [(t, [untied.note(i) for i in idx]) for t, idx in cues])
        self.settle()

        # {[2]} Checkpoint: the tie appears — one G, held through both notes
        self.say("tie")
        self.play(FadeOut(untied), FadeIn(tied), run_time=0.8)
        events, cues, _ = _events(tied_tokens, spb)
        _perform(self, events, [(t, [tied.note(i) for i in idx]) for t, idx in cues])
        self.settle()

        # {[3]} Checkpoint: the tie crosses the bar line
        bar_x = tied.barline_x(0)
        marker = Line(
            np.array([bar_x, tied.top() + 0.35, 0.0]), np.array([bar_x, tied.bottom() - 0.35, 0.0])
        ).set_stroke(HIGHLIGHT, width=8)
        self.say("barline")
        self.play(ShowCreation(marker), tied.note(2).animate.set_color(HIGHLIGHT), tied.note(3).animate.set_color(HIGHLIGHT), run_time=0.6)
        self.settle(0.6)
        self.play(FadeOut(marker), tied.note(2).animate.set_color(INK), tied.note(3).animate.set_color(INK), run_time=0.4)
        self.play(tied.animate.set_color(MUTED), run_time=0.4)  # never set_opacity: it would show the page sentinel

        # {[4]} Checkpoint: different notes, no curve — each on its own
        low = (0.55, -1.0)
        plain = _Engraved(snippet(_tiny("4/4", slur_tokens)), staff_space=0.38, max_width=11.6, center=low)
        slurred = _Engraved(_decorate(snippet(_tiny("4/4", slur_tokens)), slurs=[(0, 5)]), staff_space=0.38, max_width=11.6, center=low)
        self.play(FadeIn(plain), run_time=0.6)
        self.say("detached")
        events, cues, _ = _events(slur_tokens, spb, length=0.45)
        _perform(self, events, [(t, [plain.note(i) for i in idx]) for t, idx in cues])
        self.settle()

        # {[5]} Checkpoint: the slur — smooth and connected
        self.say("slur")
        self.play(FadeOut(plain), FadeIn(slurred), run_time=0.8)
        events, cues, _ = _events(slur_tokens, spb, length=1.04)
        _perform(self, events, [(t, [slurred.note(i) for i in idx]) for t, idx in cues])
        self.settle()

        # {[6]} Checkpoint: side by side — same pitch: tie; different pitches: slur
        self.play(tied.animate.set_color(INK), run_time=0.4)
        label_tie = _bold(self.t("label-tie"), 40, HIGHLIGHT).next_to(tied.staff_left(), LEFT, buff=0.35)
        label_slur = _bold(self.t("label-slur"), 40, HIGHLIGHT).next_to(slurred.staff_left(), LEFT, buff=0.35)
        self.play(FadeIn(label_tie, shift=UP * 0.1), FadeIn(label_slur, shift=DOWN * 0.1), run_time=0.5)
        self.caption("compare", extra=1.0)

        # {[7]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 2. Dots and double dots: a beat ruler (as in rudiments-1 DotsAndTies)


class _Ruler:
    """`beats` beats from x0 to x1; rows of glyphs placed at start beats."""

    def __init__(self, x0: float = -3.4, x1: float = 5.8, beats: int = 4):
        self.x0, self.x1, self.beats = x0, x1, beats

    def x(self, beat: float) -> float:
        return self.x0 + (self.x1 - self.x0) * beat / self.beats

    def numbers(self, y: float) -> VGroup:
        return VGroup(*(words(str(b + 1), LABEL_SIZE, MUTED).move_to(np.array([self.x(b) + 0.15, y, 0.0])) for b in range(self.beats)))

    def ticks(self, y_top: float, y_bottom: float) -> VGroup:
        return VGroup(
            *(
                Line(np.array([self.x(b), y_top, 0.0]), np.array([self.x(b), y_bottom, 0.0])).set_stroke(MUTED, width=1.5, opacity=0.5)
                for b in range(self.beats + 1)
            )
        )

    def bar(self, start: float, length: float, y: float, color=BLUE, opacity: float = 0.35) -> RoundedRectangle:
        bar = RoundedRectangle(
            width=(self.x1 - self.x0) * length / self.beats - 0.1, height=0.16, corner_radius=0.08,
            fill_color=color, fill_opacity=opacity, stroke_width=0,
        )
        return bar.move_to(np.array([self.x(start) + bar.get_width() / 2 + 0.05, y - 0.3, 0.0]))

    def glyph(self, name: str, beat: float, y: float, staff_space: float = 0.28) -> SmuflGlyph:
        glyph = SmuflGlyph(name, staff_space=staff_space)
        glyph.shift(np.array([self.x(beat) + 0.1, y, 0.0]) - glyph.origin())
        return glyph


def _dots(note: SmuflGlyph, count: int, staff_space: float = 0.28) -> VGroup:
    """Augmentation dots right of a note glyph's head, in the space above
    the head's line (the head sits on the ruler row as on a line)."""
    head_right = note.origin()[0] + 1.18 * staff_space
    group = VGroup()
    for k in range(count):
        dot = SmuflGlyph("augmentationDot", staff_space=staff_space)
        dot.move_to(np.array([head_right + (0.45 + 0.7 * k) * staff_space, note.origin()[1] + 0.5 * staff_space, 0.0]))
        group.add(dot)
    return group


class DotsAndDoubleDots(_Lesson):
    def construct(self):
        spb = 0.75
        ruler = _Ruler()
        rows_y = (1.5, 0.05, -1.4)

        # {[1]} Checkpoint: title and the four-beat ruler
        self.title()
        numbers = ruler.numbers(2.55)
        self.play(FadeIn(ruler.ticks(2.25, -1.95)), FadeIn(numbers), run_time=0.6)

        def sweep(segments, notes_events):
            """segments: (start beat, mobjects) lit in turn; clicks on every beat."""
            clicks = [(b * spb, ("click",), 0.1, 70) for b in range(4)]
            events = clicks + [(s * spb, ("C5",), d * spb * 0.95, 76) for s, d in notes_events]
            cues = [(s * spb, mobs) for s, mobs in segments]
            beat_actions = []
            for b in range(4):
                beat_actions.append((b * spb, lambda b=b: [n.set_color(HIGHLIGHT if k == b else MUTED) for k, n in enumerate(numbers)]))
            _perform(self, events, cues, actions=beat_actions, tail=0.4)
            for n in numbers:
                n.set_color(MUTED)

        # {[2]} Checkpoint: half + half — 2 beats each
        y = rows_y[0]
        h1, h2 = ruler.glyph("noteHalfUp", 0, y), ruler.glyph("noteHalfUp", 2, y)
        bars1 = VGroup(ruler.bar(0, 2, y), ruler.bar(2, 2, y))
        label1 = _bold(self.t("label-2"), 44, HIGHLIGHT).move_to(np.array([-5.4, y + 0.35, 0.0]))
        self.play(FadeIn(VGroup(h1, h2, bars1, label1)), run_time=0.5)
        self.say("half")
        sweep([(0, [h1]), (2, [h2])], [(0, 2), (2, 2)])
        self.settle()

        # {[3]} Checkpoint: dotted half + quarter — the dot adds one beat
        y = rows_y[1]
        d1 = ruler.glyph("noteHalfUp", 0, y)
        dot1 = _dots(d1, 1)
        q = ruler.glyph("noteQuarterUp", 3, y)
        base = ruler.bar(0, 2, y)
        extra = ruler.bar(2, 1, y, color=HIGHLIGHT, opacity=0.7)
        tail = ruler.bar(3, 1, y)
        label2 = _bold(self.t("label-3"), 44, HIGHLIGHT).move_to(np.array([-5.4, y + 0.35, 0.0]))
        self.play(FadeIn(VGroup(d1, q, base, tail)), run_time=0.4)
        self.say("dot")
        self.play(FadeIn(dot1, scale=2.0), run_time=0.5)
        self.play(GrowFromPoint(extra, extra.get_left()), FadeIn(label2), run_time=0.6)
        sweep([(0, [d1, dot1]), (3, [q])], [(0, 3), (3, 1)])
        self.settle()

        # {[4]} Checkpoint: double-dotted half + eighth — the second dot adds half a beat
        y = rows_y[2]
        dd = ruler.glyph("noteHalfUp", 0, y)
        dots2 = _dots(dd, 2)
        e8 = ruler.glyph("note8thUp", 3.5, y)
        base2 = ruler.bar(0, 2, y)
        extra2a = ruler.bar(2, 1, y, color=HIGHLIGHT, opacity=0.7)
        extra2b = ruler.bar(3, 0.5, y, color=ORANGE, opacity=0.7)
        tail2 = ruler.bar(3.5, 0.5, y)
        label3 = _bold(self.t("label-35"), 44, HIGHLIGHT).move_to(np.array([-5.4, y + 0.35, 0.0]))
        self.play(FadeIn(VGroup(dd, e8, base2, tail2, dots2[0], extra2a)), run_time=0.4)
        self.say("double")
        self.play(FadeIn(dots2[1], scale=2.0), dots2[1].animate.set_color(ORANGE), run_time=0.5)
        self.play(GrowFromPoint(extra2b, extra2b.get_left()), FadeIn(label3), run_time=0.6)
        self.wait(0.8)
        sweep([(0, [dd, dots2]), (3.5, [e8])], [(0, 3.5), (3.5, 0.5)])
        dots2[1].set_color(ORANGE)
        self.settle()

        # {[5]} Checkpoint: every row ends on the same line
        end = Line(np.array([ruler.x(4), 2.25, 0.0]), np.array([ruler.x(4), -1.95, 0.0])).set_stroke(HIGHLIGHT, width=6)
        self.say("fill")
        self.play(ShowCreation(end), run_time=0.5)
        self.settle(0.6)

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 3. Articulation: plain bar, then the same bar marked


_ART_TOKENS = ["C5:4", "D5:4", "E5:4", "C5:4"] * 2


class ArticulationMarks(_Lesson):
    def construct(self):
        spb = 0.6
        center = (0.0, 0.55)
        xml = snippet(_tiny("4/4", _ART_TOKENS))

        def score(marks=None):
            return _Engraved(_decorate(xml, marks), staff_space=0.44, center=center, spacing=(0.25, 0.52))

        def label(music, m, key, color):
            x0, x1 = music.measure_span(m)
            return _bold(self.t(key), 40, color).move_to(np.array([(x0 + x1) / 2, music.bottom() - 1.05, 0.0]))

        def play(music, per_bar2):
            plain_events, plain_cues, end = _events(_ART_TOKENS[:4], spb, velocity=72, length=0.85)
            marked_events, marked_cues, _ = _events(_ART_TOKENS[4:], spb, start=end, **per_bar2)
            cues = [(t, [music.note(i) for i in idx]) for t, idx in plain_cues]
            cues += [(t, [music.note(i + 4) for i in idx]) for t, idx in marked_cues]
            _perform(self, plain_events + marked_events, cues)

        # {[1]} Checkpoint: title; the same bar twice, both plain
        self.title()
        current = score()
        left = label(current, 0, "label-plain", MUTED)
        right = label(current, 1, "label-plain", MUTED)
        self.play(FadeIn(current), FadeIn(left), FadeIn(right), run_time=0.6)
        self.say("plain")
        play(current, dict(velocity=72, length=0.85))
        self.settle()

        rounds = (
            ("staccato", "label-staccato", {i: ["staccato"] for i in range(4, 8)}, dict(velocity=72, length=0.18)),
            ("tenuto", "label-tenuto", {i: ["tenuto"] for i in range(4, 8)}, dict(velocity=80, length=1.0)),
            ("accent", "label-accent", {4: ["accent"], 6: ["accent"]}, dict(velocity=56, length=0.85, per={0: dict(velocity=112), 2: dict(velocity=112)})),
            ("marcato", "label-marcato", {4: ["strong-accent"], 6: ["strong-accent"]}, dict(velocity=56, length=0.85, per={0: dict(velocity=127, length=0.6), 2: dict(velocity=127, length=0.6)})),
        )
        for index, (key, label_key, marks, sound) in enumerate(rounds, start=2):
            # {[2]} Checkpoint: staccato, tenuto, accent, marcato — one round each (marks appear, both bars play)
            marked = score(marks)
            new_right = label(marked, 1, label_key, HIGHLIGHT)
            self.say(key)
            self.play(FadeOut(current), FadeIn(marked), FadeOut(right), FadeIn(new_right), run_time=0.7)
            current, right = marked, new_right
            play(current, sound)
            self.settle(0.6)

        # {[3]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 4. The dynamics ladder

_LADDER = (
    ("dynamicPPP", 24),
    ("dynamicPP", 36),
    ("dynamicPiano", 50),
    ("dynamicMP", 64),
    ("dynamicMF", 80),
    ("dynamicForte", 96),
    ("dynamicFF", 112),
    ("dynamicFFF", 127),
)
_CHORD = ("C3", "G3", "C4", "E4", "G4")


class DynamicsLadder(_Lesson):
    def construct(self):
        ss = 0.42
        glyph_y, bar_floor = -1.0, -0.45

        # {[1]} Checkpoint: title; build the ladder layout (hidden)
        self.title()
        glyphs = [SmuflGlyph(name, staff_space=ss) for name, _ in _LADDER]
        gap = 0.75 * ss
        total = sum(g.get_width() for g in glyphs) + gap * (len(glyphs) - 1)
        x = -total / 2
        for g in glyphs:
            g.shift(np.array([x - g.get_left()[0], glyph_y - g.origin()[1], 0.0]))
            x += g.get_width() + gap
        bars = []
        for i, g in enumerate(glyphs):
            height = 0.3 + 0.33 * i
            bar = Rectangle(width=min(g.get_width(), 1.0), height=height, fill_color=BLUE, fill_opacity=0.35, stroke_width=0)
            bar.move_to(np.array([g.get_center()[0], bar_floor + height / 2, 0.0]))
            bars.append(bar)
        rung = [VGroup(g, b) for g, b in zip(glyphs, bars)]

        def light(i, on):
            glyphs[i].set_color(HIGHLIGHT if on else INK)
            bars[i].set_fill(HIGHLIGHT if on else BLUE, opacity=0.8 if on else 0.35)

        def hit(indices, seconds=1.1):
            """Each mark sounds the same chord at its own velocity, lit while it rings."""
            events = [(k * seconds, _CHORD, seconds * 0.9, _LADDER[i][1]) for k, i in enumerate(indices)]
            actions = []
            for k, i in enumerate(indices):
                def step(k=k, i=i):
                    if k:
                        light(indices[k - 1], False)
                    light(i, True)
                actions.append((k * seconds, step))
            _perform(self, events, [], actions=actions, tail=0.3)
            light(indices[-1], False)

        def label(key, x, color=INK):
            return words(self.t(key), 38, color).move_to(np.array([x, -1.9, 0.0]))

        # {[2]} Checkpoint: p and f — soft and loud, heard
        p_label = label("label-p", glyphs[2].get_center()[0])
        f_label = label("label-f", glyphs[5].get_center()[0])
        self.play(FadeIn(rung[2]), FadeIn(rung[5]), FadeIn(p_label), FadeIn(f_label), run_time=0.6)
        self.say("piano-forte")
        hit([2, 5, 2, 5])
        self.settle()

        # {[3]} Checkpoint: mezzo — mp and mf in between
        m_label = label("label-m", (glyphs[3].get_center()[0] + glyphs[4].get_center()[0]) / 2)
        self.play(FadeOut(p_label), FadeOut(f_label), FadeIn(rung[3]), FadeIn(rung[4]), FadeIn(m_label), run_time=0.6)
        self.say("mezzo")
        hit([2, 3, 4, 5])
        self.settle()

        # {[4]} Checkpoint: more letters — pp ppp, ff fff
        self.play(FadeOut(m_label), *(FadeIn(rung[i]) for i in (0, 1, 6, 7)), run_time=0.6)
        self.say("more")
        hit([2, 1, 0, 5, 6, 7], seconds=0.95)
        self.settle()

        # {[5]} Checkpoint: the whole climb, softest to loudest
        self.say("climb")
        hit(list(range(8)), seconds=0.85)
        self.settle()

        # {[6]} Checkpoint: relative — p and f only mean softer and louder
        self.say("relative")
        self.play(*(r.animate.set_opacity(0.25) for i, r in enumerate(rung) if i not in (2, 5)), run_time=0.5)
        hit([2, 5])
        self.settle(0.6)

        # {[7]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 5. Hairpins and sf


def _hairpin(x0: float, x1: float, y: float, opening: float, growing: bool = True) -> VGroup:
    """Two lines from a point to an opening (crescendo) or the reverse."""
    tip, mouth = (x0, x1) if growing else (x1, x0)
    upper = Line(np.array([tip, y, 0.0]), np.array([mouth, y + opening / 2, 0.0]))
    lower = Line(np.array([tip, y, 0.0]), np.array([mouth, y - opening / 2, 0.0]))
    return VGroup(upper, lower).set_stroke(INK, width=5)


class CrescendoAndSforzando(_Lesson):
    def construct(self):
        spb = 0.5
        center = (0.0, 0.9)

        def bars_of(pitches):
            return _Bars([[(p, "quarter") for p in pitches[:4]], [(p, "quarter") for p in pitches[4:]]], center=center)

        def dyn(bars, name, i, below):
            glyph = SmuflGlyph(name, staff_space=bars.ss)
            glyph.shift(np.array([bars.head_x(i), below, 0.0]) - glyph.get_center() * np.array([1, 0, 0]) - glyph.origin() * np.array([0, 1, 0]))
            return glyph

        def ramp(bars, velocities):
            events = [(i * spb, (p,), spb * 0.9, v) for i, (p, v) in enumerate(zip(bars.pitches, velocities))]
            cues = [(i * spb, [n]) for i, n in enumerate(bars.notes)]
            _perform(self, events, cues)

        # {[1]} Checkpoint: title; a rising line with p, an opening hairpin, f
        self.title()
        rising = bars_of(["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"])
        base = rising.y(-2) - 1.75 * rising.ss - 0.25
        p1, f1 = dyn(rising, "dynamicPiano", 0, base), dyn(rising, "dynamicForte", 7, base)
        mid = base + 0.3 * rising.ss
        cresc = _hairpin(p1.get_right()[0] + 0.35, f1.get_left()[0] - 0.35, mid, 1.5 * rising.ss)
        self.play(FadeIn(rising), FadeIn(p1), FadeIn(f1), run_time=0.6)
        self.say("crescendo")
        self.play(ShowCreation(cresc), run_time=0.8)
        ramp(rising, [int(v) for v in np.linspace(38, 118, 8)])
        self.settle()

        # {[2]} Checkpoint: the word cresc. in place of the hairpin
        word = _italic(self.t("cresc-word"), 52).move_to(np.array([cresc.get_center()[0], mid + 0.05, 0.0]))
        self.say("cresc-same")
        self.play(FadeOut(cresc), FadeIn(word), run_time=0.6)
        self.settle(0.6)
        self.play(FadeOut(VGroup(rising, p1, f1, word)), run_time=0.5)

        # {[3]} Checkpoint: falling line, f, a closing hairpin, p
        falling = bars_of(["C5", "B4", "A4", "G4", "F4", "E4", "D4", "C4"])
        f2, p2 = dyn(falling, "dynamicForte", 0, base), dyn(falling, "dynamicPiano", 7, base)
        dim = _hairpin(f2.get_right()[0] + 0.35, p2.get_left()[0] - 0.35, mid, 1.5 * falling.ss, growing=False)
        self.play(FadeIn(falling), FadeIn(f2), FadeIn(p2), run_time=0.6)
        self.say("diminuendo")
        self.play(ShowCreation(dim), run_time=0.8)
        ramp(falling, [int(v) for v in np.linspace(118, 38, 8)])
        self.settle()

        # {[4]} Checkpoint: the word dim.
        word = _italic(self.t("dim-word"), 52).move_to(np.array([dim.get_center()[0], mid + 0.05, 0.0]))
        self.say("dim-same")
        self.play(FadeOut(dim), FadeIn(word), run_time=0.6)
        self.settle(0.6)
        self.play(FadeOut(VGroup(falling, f2, p2, word)), run_time=0.5)

        # {[5]} Checkpoint: sf — one sudden strong note in a soft line
        line = bars_of(["C5", "G4", "E4", "G4", "C5", "G4", "E4", "G4"])
        p3 = dyn(line, "dynamicPiano", 0, base)
        sf = dyn(line, "dynamicSforzando1", 4, base)  # "sf" (dynamicSforzando is the bare s)
        sf.set_color(HIGHLIGHT)
        self.play(FadeIn(line), FadeIn(p3), run_time=0.6)
        self.say("sforzando")
        self.play(FadeIn(sf, scale=1.4), run_time=0.5)
        velocities = [44] * 8
        velocities[4] = 124
        for _ in range(2):
            ramp(line, velocities)
            self.wait(0.3)
        self.settle()

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 6-8. The road map: repeats, endings, D.C., D.S., Fine, Coda


def _jump(from_x: float, to_x: float, y: float, angle: float) -> CurvedArrow:
    """A stroked arc with a tip: the road turning (positive angle bends
    a right-to-left arc upward, negative a left-to-right one)."""
    arrow = CurvedArrow(np.array([from_x, y, 0.0]), np.array([to_x, y, 0.0]), angle=angle, stroke_color=HIGHLIGHT, stroke_width=6)
    arrow.tip.set_fill(HIGHLIGHT, opacity=1.0)
    return arrow


def _numbers(bars: _Bars, y: float, count: int) -> VGroup:
    return VGroup(*(words(str(m + 1), SMALL_SIZE, MUTED).move_to(np.array([sum(bars.span(m)) / 2, y, 0.0])) for m in range(count)))


def _trace(scene, bars: _Bars, order, spb: float, low: float, high: float, numbers: VGroup, jumps=()):
    """Play measures in `order` with a box riding over the current measure,
    its number lit; `jumps` = [(position in order, arrow)] appear when the
    road turns there."""
    events, cues, starts, _ = _route(bars, order, spb)
    box = _measure_box(bars, order[0], low, high)
    scene.add(box)
    actions = []
    for position, (t, m) in enumerate(starts):
        def go(m=m, position=position):
            box.become(_measure_box(bars, m, low, high))
            for k, n in enumerate(numbers):
                n.set_color(HIGHLIGHT if k == m else MUTED)
            for at, arrow in jumps:
                if at == position:
                    scene.add(arrow)
        actions.append((t, go))
    _perform(scene, events, cues, actions=actions, tail=0.6)
    scene.play(FadeOut(box), *(FadeOut(a) for _, a in jumps), run_time=0.4)
    for n in numbers:
        n.set_color(MUTED)


def _road_layout(bars: _Bars):
    """Shared vertical layout of the road-map videos: (box low, box high,
    numbers y, words y, arrows y)."""
    low = bars.music_bottom() - 0.2
    return low, bars.y(10.3), low - 0.32, bars.y(12.5), bars.y(15.0)


class RepeatsAndEndings(_Lesson):
    def construct(self):
        spb = 0.5
        bars = _Bars(
            [[("E4", "half"), ("G4", "half")], [("F4", "half"), ("D4", "half")], [("C4", "whole")]],
            ends=["single", "repeat", "final"],
            staff_space=0.46,
            center=(0.0, -0.1),
            max_width=12.4,
        )
        low, high, numbers_y, _, arrow_y = _road_layout(bars)
        numbers = _numbers(bars, numbers_y, 3)

        # {[1]} Checkpoint: title; three measures and a repeat sign
        self.title()
        bracket_y = bars.y(12.7)
        brackets, ending_labels = VGroup(), VGroup()
        for m, key, closed in ((1, "ending-1", True), (2, "ending-2", False)):
            x0, x1 = bars.span(m)
            x0, x1 = x0 + 0.08, x1 - 0.2
            hook = 1.2 * bars.ss
            corner = np.array([x0, bracket_y, 0.0])
            group = VGroup(Line(corner + DOWN * hook, corner), Line(corner, np.array([x1, bracket_y, 0.0])))
            if closed:
                group.add(Line(np.array([x1, bracket_y, 0.0]), np.array([x1, bracket_y - hook, 0.0])))
            brackets.add(group.set_stroke(INK, width=3))
            label = _bold(self.t(key), LABEL_SIZE, INK)
            ending_labels.add(label.move_to(corner + np.array([0.2 + label.get_width() / 2, -0.32, 0.0])))
        self.play(FadeIn(bars), FadeIn(numbers), run_time=0.6)

        # {[2]} Checkpoint: the repeat sign, ringed
        sign = bars.bar_glyphs[1]
        ring = RoundedRectangle(width=sign.get_width() + 0.5, height=sign.get_height() + 0.5, corner_radius=0.15, stroke_color=HIGHLIGHT, stroke_width=5)
        ring.move_to(sign)
        self.say("repeat")
        self.play(ShowCreation(ring), sign.animate.set_color(HIGHLIGHT), run_time=0.6)
        self.settle()
        self.play(FadeOut(ring), sign.animate.set_color(INK), run_time=0.4)

        # {[3]} Checkpoint: the endings appear; first time through: 1, then ending 1
        self.play(ShowCreation(brackets), FadeIn(ending_labels), run_time=0.7)
        self.say("first")
        _trace(self, bars, [0, 1], spb, low, high, numbers)
        self.settle(0.2)

        # {[4]} Checkpoint: the jump back to the start
        back = _jump(sign.get_center()[0], bars.span(0)[0] + 0.5, arrow_y, PI / 7)
        self.say("back")
        self.play(ShowCreation(back), run_time=0.8)
        self.settle(0.2)
        self.play(FadeOut(back), run_time=0.3)

        # {[5]} Checkpoint: second time: 1, skip ending 1, play ending 2
        self.say("second")
        skip = _jump(bars.span(0)[1] - 0.15, bars.span(2)[0] + 0.45, arrow_y, -PI / 4)
        self.play(brackets[0].animate.set_color(MUTED), ending_labels[0].animate.set_color(MUTED), run_time=0.4)
        _trace(self, bars, [0, 2], spb, low, high, numbers, jumps=[(1, skip)])
        self.settle(0.2)
        self.play(brackets[0].animate.set_color(INK), ending_labels[0].animate.set_color(INK), run_time=0.3)

        # {[6]} Checkpoint: the whole road in one go
        self.say("order")
        whole_back = _jump(sign.get_center()[0], bars.span(0)[0] + 0.5, arrow_y, PI / 7)
        skip2 = _jump(bars.span(0)[1] - 0.15, bars.span(2)[0] + 0.45, arrow_y, -PI / 4)
        _trace(self, bars, [0, 1, 0, 2], spb, low, high, numbers, jumps=[(2, whole_back), (3, skip2)])
        self.settle()

        # {[7]} Checkpoint: remember
        self.remember()


class DaCapoAlFine(_Lesson):
    def construct(self):
        spb = 0.5
        bars = _Bars(
            [[("G4", "half"), ("E4", "half")], [("D4", "half"), ("C4", "half")], [("E4", "half"), ("F4", "half")]],
            ends=["single", "double", "final"],
            staff_space=0.46,
            center=(0.0, -0.1),
            max_width=12.4,
        )
        low, high, numbers_y, words_y, arrow_y = _road_layout(bars)
        numbers = _numbers(bars, numbers_y, 3)
        fine = _italic(self.t("fine-word"), 40, weight="BOLD")
        fine.move_to(np.array([bars.span(1)[1] - fine.get_width() / 2, words_y, 0.0]))
        dc = _italic(self.t("dc-word"), 40, weight="BOLD")
        dc.move_to(np.array([bars.span(2)[1] - dc.get_width() / 2, words_y, 0.0]))

        # {[1]} Checkpoint: title; three measures with Fine and D.C. al Fine
        self.title()
        self.play(FadeIn(bars), FadeIn(numbers), FadeIn(fine), FadeIn(dc), run_time=0.6)

        # {[2]} Checkpoint: straight through to the end of the line
        self.say("play")
        _trace(self, bars, [0, 1, 2], spb, low, high, numbers)
        self.settle(0.2)

        # {[3]} Checkpoint: D.C. — back to the head
        back = _jump(dc.get_center()[0], bars.span(0)[0] + 0.5, arrow_y, PI / 7)
        self.say("dc")
        self.play(dc.animate.set_color(HIGHLIGHT), run_time=0.3)
        self.play(ShowCreation(back), run_time=0.8)
        self.settle(0.2)
        self.play(FadeOut(back), dc.animate.set_color(INK), run_time=0.3)

        # {[4]} Checkpoint: play again until Fine, and stop
        self.say("fine")
        _trace(self, bars, [0, 1], spb, low, high, numbers)
        self.play(fine.animate.set_color(HIGHLIGHT), run_time=0.3)
        self.settle(0.4)
        self.play(fine.animate.set_color(INK), run_time=0.3)

        # {[5]} Checkpoint: the whole road in one go
        self.say("order")
        whole_back = _jump(dc.get_center()[0], bars.span(0)[0] + 0.5, arrow_y, PI / 7)
        _trace(self, bars, [0, 1, 2, 0, 1], spb, low, high, numbers, jumps=[(3, whole_back)])
        self.settle()

        # {[6]} Checkpoint: remember
        self.remember()


class DalSegnoAlCoda(_Lesson):
    def construct(self):
        spb = 0.5
        bars = _Bars(
            [[("C4", "half"), ("E4", "half")], [("G4", "half"), ("A4", "half")], [("G4", "half"), ("F4", "half")], [("C5", "whole")]],
            ends=["single", "single", "double", "final"],
            staff_space=0.42,
            gaps={3: 2.6},
            center=(0.0, -0.1),
            max_width=12.8,
        )
        low, high, numbers_y, _, arrow_y = _road_layout(bars)
        words_y = bars.y(13.1)  # clear of the A's stem in bar 2
        numbers = _numbers(bars, numbers_y, 4)
        numbers[3].become(words(self.t("coda-word"), SMALL_SIZE, MUTED).move_to(numbers[3]))
        sign_ss = 0.6 * bars.ss
        segno = SmuflGlyph("segno", staff_space=sign_ss)
        segno.move_to(np.array([bars.span(1)[0], bars.y(10.6) + segno.get_height() / 2, 0.0]))  # over the bar line where the road resumes
        to_coda = VGroup(_italic(self.t("tocoda-word"), 28, weight="BOLD"), SmuflGlyph("coda", staff_space=0.42 * bars.ss))
        to_coda.arrange(RIGHT, buff=0.1)
        to_coda.move_to(np.array([bars.span(1)[1] - 0.05 - to_coda.get_width() / 2, words_y, 0.0]))
        ds = _italic(self.t("ds-word"), 28, weight="BOLD")
        ds.move_to(np.array([bars.span(2)[1] - 0.1 - ds.get_width() / 2, words_y, 0.0]))
        coda = SmuflGlyph("coda", staff_space=sign_ss)
        coda.move_to(np.array([bars.span(3)[0] + 0.1 + coda.get_width() / 2, bars.y(10.6) + coda.get_height() / 2, 0.0]))
        signs = VGroup(segno, to_coda, ds, coda)

        # {[1]} Checkpoint: title; the music with its road signs, segno and coda lit
        self.title()
        self.play(FadeIn(bars), FadeIn(numbers), FadeIn(signs), run_time=0.6)
        self.say("signs")
        self.play(segno.animate.set_color(HIGHLIGHT), coda.animate.set_color(HIGHLIGHT), run_time=0.5)
        self.settle()
        self.play(segno.animate.set_color(INK), coda.animate.set_color(INK), run_time=0.3)

        # {[2]} Checkpoint: straight through, past To Coda
        self.say("play")
        _trace(self, bars, [0, 1, 2], spb, low, high, numbers)
        self.settle(0.2)

        # {[3]} Checkpoint: D.S. — back to the sign
        back = _jump(ds.get_center()[0], segno.get_center()[0], arrow_y, PI / 4)
        self.say("ds")
        self.play(ds.animate.set_color(HIGHLIGHT), segno.animate.set_color(HIGHLIGHT), run_time=0.3)
        self.play(ShowCreation(back), run_time=0.8)
        self.settle(0.2)
        self.play(FadeOut(back), ds.animate.set_color(INK), segno.animate.set_color(INK), run_time=0.3)

        # {[4]} Checkpoint: from the sign to To Coda, then the jump to the coda
        jump = _jump(to_coda[1].get_center()[0], coda.get_center()[0], arrow_y, -PI / 4)
        self.say("tocoda")
        self.play(to_coda.animate.set_color(HIGHLIGHT), run_time=0.3)
        _trace(self, bars, [1, 3], spb, low, high, numbers, jumps=[(1, jump)])
        to_coda.set_color(INK)
        self.settle(0.2)

        # {[5]} Checkpoint: the whole road in one go
        self.say("order")
        b2 = _jump(ds.get_center()[0], segno.get_center()[0], arrow_y, PI / 4)
        j2 = _jump(to_coda[1].get_center()[0], coda.get_center()[0], arrow_y, -PI / 4)
        _trace(self, bars, [0, 1, 2, 1, 3], spb, low, high, numbers, jumps=[(3, b2), (4, j2)])
        self.settle()

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 9. The fermata


class TheFermata(_Lesson):
    def construct(self):
        spb = 0.55
        bars = _Bars(
            [[("C5", "quarter"), ("B4", "quarter"), ("A4", "quarter"), ("G4", "quarter")],
             [("F4", "quarter"), ("E4", "quarter"), ("D4", "half")],
             [("C4", "whole")]],
            staff_space=0.44,
            center=(0.0, 0.3),
        )
        hold = 6  # the D, last note of the phrase before the close

        def play(extra_beats):
            events, cues, t = [], [], 0.0
            for i, pitch in enumerate(bars.pitches):
                beats = bars.beats[i] + (extra_beats if i == hold else 0.0)
                events.append((t, (pitch,), beats * spb * 0.95, 74))
                cues.append((t, [bars.notes[i]]))
                t += beats * spb
            _perform(self, events, cues, tail=0.4)

        # {[1]} Checkpoint: title; the phrase in strict time
        self.title()
        self.play(FadeIn(bars), run_time=0.6)
        self.say("plain")
        play(0.0)
        self.settle()

        # {[2]} Checkpoint: the fermata appears over the D — held longer
        fermata = SmuflGlyph("fermataAbove", staff_space=bars.ss, color=HIGHLIGHT)
        fermata.move_to(np.array([bars.head_x(hold), max(bars.top(), bars.notes[hold].get_top()[1]) + 0.55, 0.0]))
        self.say("fermata")
        self.play(FadeIn(fermata, shift=DOWN * 0.2), run_time=0.6)
        play(4.0)
        self.settle()

        # {[3]} Checkpoint: how long is a choice — a shorter hold
        self.say("howlong")
        play(2.0)
        self.settle()

        # {[4]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 10. Octave signs


def _octave_line(bars: _Bars, glyph_name: str, first: int, last: int, above: bool, extra_ss: float = 1.6):
    """8va / 8vb glyph with a dashed line to the end of note `last` and a
    hook pointing back at the staff."""
    ss = bars.ss
    glyph = SmuflGlyph(glyph_name, staff_space=ss)
    notes = bars.notes[first:last + 1]
    if above:
        y = max(n.get_top()[1] for n in notes) + 0.45
        glyph.shift(np.array([bars.notes[first].get_left()[0], y, 0.0]) - glyph.get_corner(DOWN + LEFT))
    else:
        y = min(n.get_bottom()[1] for n in notes) - 0.45
        glyph.shift(np.array([bars.notes[first].get_left()[0], y, 0.0]) - glyph.get_corner(UP + LEFT))
    line_y = glyph.get_center()[1]
    x_end = bars.notes[last].get_right()[0] + extra_ss * ss * 0.5
    dashes = DashedLine(np.array([glyph.get_right()[0] + 0.15, line_y, 0.0]), np.array([x_end, line_y, 0.0]), dash_length=0.12)
    hook_to = line_y - 0.45 if above else line_y + 0.45
    hook = Line(np.array([x_end, line_y, 0.0]), np.array([x_end, hook_to, 0.0]))
    lines = VGroup(dashes, hook).set_stroke(INK, width=3)
    return VGroup(glyph, lines)


class OctaveSigns(_Lesson):
    def construct(self):
        spb = 0.5
        motif = ("E", "F", "G")

        def play(bars, sounding, start_lit=0):
            events, cues, t = [], [], 0.0
            for i, pitch in enumerate(sounding):
                events.append((t, (pitch,), bars.beats[i + start_lit] * spb * 0.92, 76))
                cues.append((t, [bars.notes[i + start_lit]]))
                t += bars.beats[i + start_lit] * spb
            _perform(self, events, cues, tail=0.4)

        def measure(octave):
            return [(f"{motif[0]}{octave}", "quarter"), (f"{motif[1]}{octave}", "quarter"), (f"{motif[2]}{octave}", "half")]

        # {[1]} Checkpoint: title; high notes on a pile of ledger lines
        self.title()
        high = _Bars([measure(6)], staff_space=0.44, center=(0.0, -0.4))
        self.play(FadeIn(high), run_time=0.6)
        self.say("high")
        play(high, ["E6", "F6", "G6"])
        self.settle()

        # {[2]} Checkpoint: the same sounds written an octave lower under 8va
        written = _Bars([measure(5), measure(5)], staff_space=0.44, center=(0.0, -0.4))
        bracket = _octave_line(written, "ottavaAlta", 0, 2, above=True)
        first_bar = VGroup(*written.notes[:3])
        rest_of_staff = VGroup(*(m for m in written if m not in written.notes[3:] and m is not written.bar_glyphs[0]))
        self.say("ottava")
        self.play(FadeOut(high), FadeIn(rest_of_staff), FadeIn(bracket), run_time=0.8)
        play(written, ["E6", "F6", "G6"])
        self.settle()

        # {[3]} Checkpoint: same sound, easier to read
        self.say("same")
        self.play(bracket[0].animate.set_color(HIGHLIGHT), first_bar.animate.set_color(HIGHLIGHT), run_time=0.4)
        self.settle(0.3)
        self.play(bracket[0].animate.set_color(INK), first_bar.animate.set_color(INK), run_time=0.3)

        # {[4]} Checkpoint: the line ends — the next bar sounds as written
        self.say("loco")
        self.play(FadeIn(VGroup(*written.notes[3:], written.bar_glyphs[0])), bracket[1][1].animate.set_color(HIGHLIGHT), run_time=0.6)
        play(written, ["E6", "F6", "G6", "E5", "F5", "G5"])
        self.settle(0.2)
        bracket[1][1].set_color(INK)

        # {[5]} Checkpoint: the old word loco
        loco = _italic(self.t("loco-word"), 40, HIGHLIGHT, weight="BOLD")
        loco.move_to(np.array([written.head_x(3) + loco.get_width() / 2 - 0.2, bracket[0].get_center()[1], 0.0]))
        self.say("loco-old")
        self.play(FadeIn(loco, shift=DOWN * 0.15), run_time=0.5)
        self.settle(0.6)
        self.clear_stage()

        # {[6]} Checkpoint: 8vb — low notes written an octave higher
        low = _Bars([[("C3", "quarter"), ("D3", "quarter"), ("E3", "half")], [("C3", "quarter"), ("D3", "quarter"), ("E3", "half")]], clef="bass", staff_space=0.44, center=(0.0, 1.0))
        under = _octave_line(low, "ottavaBassaVb", 0, 2, above=False)
        self.play(FadeIn(low), FadeIn(under), run_time=0.6)
        self.say("bassa")
        play(low, ["C2", "D2", "E2", "C3", "D3", "E3"])
        self.settle()

        # {[7]} Checkpoint: remember
        self.remember()

"""Module 06 lessons (Gehrkens ch. VI): ornaments — the trill, the
mordents, the turn, the appoggiatura and the acciaccatura.

One idea per video; every word on screen comes from content/<lang>/.
Each ornament is shown three ways: the sign as written, the same music
written out in full notes underneath, and both played — the ornament as
real fast notes, the leaning note louder than its resolution. Both
staves are engraved by Verovio from tinyNotation snippets decorated here
with lxml (ornament signs, grace notes, accents, slurs); playback uses a
local velocity-aware renderer (`_sound`).

Trill realization: as Gehrkens reports for "most modern writers" (1914),
the trill starts on the written note; the video then shows the upper-note
start of music before about 1800.

Render (from the repo root):
    PYGLET_SHADOW_WINDOW=0 uv run manimgl courses/notation-1/modules/06-ornaments/scenes.py TheTrill -w -l
"""

from __future__ import annotations

import copy
import hashlib
import re
import subprocess

import mido
import numpy as np
from lxml import etree
from manimlib import (
    ITALIC,
    RIGHT,
    FadeIn,
    FadeOut,
    Text,
    VGroup,
)

from theoria.core.examples import snippet
from theoria.notation import engrave
from theoria.notation.glyphs import SmuflGlyph
from theoria.notation.lesson import LABEL_SIZE, LessonScene, reading_time, words
from theoria.notation.score import _Fragment
from theoria.paths import DEFAULT_SOUNDFONT, MEDIA_DIR
from theoria.theme import BLUE, FONT, HIGHLIGHT, INK, MUTED

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


_ORNAMENTS = ("trill-mark", "mordent", "inverted-mordent", "turn")


def _decorate(xml: str, marks=None, slurs=(), graces=()) -> str:
    """Decorate snippet MusicXML: `marks` {note index: [names]} — ornament
    signs ('trill-mark', 'mordent', 'inverted-mordent', 'turn', 'wavy' for
    a trill's wavy line) or articulations ('accent'...); `slurs`
    [(first, last)]; `graces` [(index, pitch, slashed)] — a small eighth
    before note `index`, slurred to it. Indices count the snippet's notes
    (not rests), before any grace note is inserted."""
    root = etree.fromstring(xml.encode())
    notes = [n for n in root.iter("note") if n.find("rest") is None]

    def notations(note):
        found = note.find("notations")
        return found if found is not None else etree.SubElement(note, "notations")

    def child(parent, tag):
        found = parent.find(tag)
        return found if found is not None else etree.SubElement(parent, tag)

    for index, names in (marks or {}).items():
        holder = notations(notes[index])
        for name in names:
            if name in _ORNAMENTS:
                etree.SubElement(child(holder, "ornaments"), name)
            elif name == "wavy":
                for kind in ("start", "stop"):
                    line = etree.SubElement(child(holder, "ornaments"), "wavy-line")
                    line.set("type", kind)
                    line.set("number", "1")
            else:
                mark = etree.SubElement(child(holder, "articulations"), name)
                if name == "strong-accent":
                    mark.set("type", "up")
    number = 1
    for first, last in slurs:
        for index, kind in ((first, "start"), (last, "stop")):
            slur = etree.SubElement(notations(notes[index]), "slur")
            slur.set("type", kind)
            slur.set("number", str(number))
        number += 1
    for index, pitch, slashed in graces:
        principal = notes[index]
        grace = copy.deepcopy(principal)
        for tag in ("duration", "notations", "tie", "beam", "dot", "time-modification", "accidental"):
            for el in grace.findall(tag):
                grace.remove(el)
        flag = etree.Element("grace")
        if slashed:
            flag.set("slash", "yes")
        grace.insert(0, flag)
        written = grace.find("pitch")
        written.find("step").text = pitch[0]
        written.find("octave").text = pitch[-1]
        if written.find("alter") is not None:
            written.remove(written.find("alter"))
        grace.find("type").text = "eighth"
        for target, kind in ((grace, "start"), (principal, "stop")):
            slur = etree.SubElement(notations(target), "slur")
            slur.set("type", kind)
            slur.set("number", str(number))
        number += 1
        principal.addprevious(grace)
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
# Written / played layouts. Short ornaments sit side by side, as in
# Gehrkens' own figures ("Written | Played"), at full staff size; the long
# trill stacks the two staves, at the size that fits both rows.


def _engrave_at(xml: str, staff_space: float, left: float, y: float) -> _Engraved:
    score = _Engraved(xml, staff_space=staff_space, max_width=99.0, center=(0.0, y))
    score.shift(RIGHT * (left - score.staff_left()[0]))
    return score


def _staff_width_ss(xml: str) -> float:
    probe = _Engraved(xml, staff_space=1.0, max_width=999.0)
    return (probe.staff_x[1] - probe.staff_x[0]) / probe.unit


def _side_by_side(scene, written_xml: str, played_xml: str, y: float = 0.25, gap: float = 1.3, width: float = 12.6, staff_space: float = 0.42):
    """(written, played, labels): two staves in a row, labels above each."""
    w1, w2 = _staff_width_ss(written_xml), _staff_width_ss(played_xml)
    ss = min(staff_space, (width - gap) / (w1 + w2))
    left = -((w1 + w2) * ss + gap) / 2
    written = _engrave_at(written_xml, ss, left, y)
    played = _engrave_at(played_xml, ss, left + w1 * ss + gap, y)
    labels = VGroup()
    for key, score, w in (("label-written", written, w1), ("label-played", played, w2)):
        label = _bold(scene.t(key), 36, MUTED)
        labels.add(label.move_to(np.array([score.staff_left()[0] + w * ss / 2, score.top() + 3.4 * ss + 0.15, 0.0])))
    return written, played, labels


def _stacked(scene, written_xml: str, played_xml: str, staff_space: float = 0.31, width: float = 11.4, also=()):
    """(written, played, labels): the sign above its written-out notes,
    left-aligned, labels at the left; sized so `played` and any
    alternative realizations (`also`) fit `width`."""
    ss = min(staff_space, width / max(_staff_width_ss(x) for x in (played_xml, *also)))
    left = -width / 2 + 0.75
    played = _engrave_at(played_xml, ss, left, -0.95)
    written = _engrave_at(written_xml, ss, left, 1.25)
    labels = VGroup()
    for key, score in (("label-written", written), ("label-played", played)):
        label = _bold(scene.t(key), 32, MUTED)
        labels.add(label.move_to(np.array([left - 0.3 - label.get_width() / 2, score.staff_left()[1], 0.0])))
    return written, played, labels


def _lit(score: _Engraved, cues, offset: int = 0):
    """Token cues (time, [note indices]) -> mobject cues on `score`."""
    return [(t, [score.note(i + offset) for i in idx]) for t, idx in cues]


# ---------------------------------------------------------------------------
# 1. The trill


class TheTrill(_Lesson):
    def construct(self):
        spb = 0.75
        written_tokens = ["D5:2", "C5:4"]
        modern = ["D5:32", "E5:32"] * 6 + ["D5:32", "C5:32", "D5:16", "C5:4"]
        older = ["E5:32", "D5:32"] * 7 + ["C5:32", "D5:32", "C5:4"]
        written, played, labels = _stacked(
            self,
            _decorate(snippet(_tiny("3/4", written_tokens)), marks={0: ["trill-mark", "wavy"]}),
            snippet(_tiny("3/4", modern)),
            also=[snippet(_tiny("3/4", older))],
        )
        upper_start = _engrave_at(snippet(_tiny("3/4", older)), played.ss, played.staff_left()[0], played.staff_left()[1])
        modern_events, modern_cues, _ = _events(modern, spb, velocity=70, length=0.95)
        older_events, older_cues, _ = _events(older, spb, velocity=70, length=0.95)
        sign_cues = [(0.0, [written.note(0)]), (2 * spb, [written.note(1)])]

        # {[1]} Checkpoint: title; the written trill, heard
        self.title()
        self.play(FadeIn(written), FadeIn(labels[0]), run_time=0.6)
        self.say("written")
        _perform(self, modern_events, sign_cues)
        self.settle()

        # {[2]} Checkpoint: written out — the note and the note above, alternating
        self.play(FadeIn(played), FadeIn(labels[1]), run_time=0.6)
        self.say("played")
        _perform(self, modern_events, _lit(played, modern_cues))
        self.settle()

        # {[3]} Checkpoint: the closing notes D C D, lit
        ending = [played.note(i) for i in (12, 13, 14)]
        self.say("ending")
        self.play(*(m.animate.set_color(BLUE) for m in ending), run_time=0.4)
        self.settle()
        self.play(*(m.animate.set_color(INK) for m in ending), run_time=0.3)

        # {[4]} Checkpoint: sign and written-out notes, back to back — the same sound
        self.say("same")
        _perform(self, modern_events, sign_cues, tail=0.3)
        _perform(self, modern_events, _lit(played, modern_cues))
        self.settle()

        # {[5]} Checkpoint: older music starts on the upper note
        self.say("older")
        self.play(FadeOut(played), FadeIn(upper_start), run_time=0.7)
        _perform(self, older_events, _lit(upper_start, older_cues))
        self.wait(0.3)
        _perform(self, older_events, _lit(upper_start, older_cues))
        self.settle()

        # {[6]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 2. The mordents


class TheMordents(_Lesson):
    def construct(self):
        spb = 0.8
        written_tokens = ["C5:4", "G4:4"]
        lower_tokens = ["C5:32", "B4:32", "C5:8.", "G4:4"]
        upper_tokens = ["C5:32", "D5:32", "C5:8.", "G4:4"]
        lower_w, lower_p, labels = _side_by_side(self, _decorate(snippet(_tiny("2/4", written_tokens)), marks={0: ["mordent"]}), snippet(_tiny("2/4", lower_tokens)))
        upper_w, upper_p, _ = _side_by_side(self, _decorate(snippet(_tiny("2/4", written_tokens)), marks={0: ["inverted-mordent"]}), snippet(_tiny("2/4", upper_tokens)))
        lower_events, lower_cues, _ = _events(lower_tokens, spb, velocity=74, length=0.95)
        upper_events, upper_cues, _ = _events(upper_tokens, spb, velocity=74, length=0.95)

        def both(written, played, events, cues):
            _perform(self, events, [(0.0, [written.note(0)]), (spb, [written.note(1)])], tail=0.3)
            _perform(self, events, _lit(played, cues))

        # {[1]} Checkpoint: title; the mordent with its line, written and played
        self.title()
        self.play(FadeIn(lower_w), FadeIn(lower_p), FadeIn(labels), run_time=0.6)
        self.say("lower")
        both(lower_w, lower_p, lower_events, lower_cues)
        self.settle()

        # {[2]} Checkpoint: fast — the held rest of the note lit
        self.say("fast")
        flick = VGroup(lower_p.note(0), lower_p.note(1))
        self.play(flick.animate.set_color(BLUE), run_time=0.3)
        self.wait(0.6)
        self.play(flick.animate.set_color(INK), lower_p.note(2).animate.set_color(HIGHLIGHT), run_time=0.3)
        self.settle(0.2)
        self.play(lower_p.note(2).animate.set_color(INK), run_time=0.3)

        # {[3]} Checkpoint: without the line — up to the note above
        self.say("upper")
        self.play(FadeOut(lower_w), FadeOut(lower_p), FadeIn(upper_w), FadeIn(upper_p), run_time=0.7)
        both(upper_w, upper_p, upper_events, upper_cues)
        self.settle()
        self.clear_stage()

        # {[4]} Checkpoint: the two signs side by side, each heard
        signs = VGroup()
        for glyph_name, key, x in (("ornamentMordent", "label-lower", -3.2), ("ornamentShortTrill", "label-upper", 3.2)):
            glyph = SmuflGlyph(glyph_name, staff_space=1.1)
            glyph.move_to(np.array([x, 0.9, 0.0]))
            label = _bold(self.t(key), 40, INK).move_to(np.array([x, -0.6, 0.0]))
            signs.add(VGroup(glyph, label))
        self.play(FadeIn(signs), run_time=0.6)
        self.say("compare")
        for k, (events, cues) in enumerate(((lower_events, lower_cues), (upper_events, upper_cues))):
            _perform(self, events, [(0.0, [signs[k]])], tail=0.6)
        self.settle()

        # {[5]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 3. The turn


class TheTurn(_Lesson):
    def construct(self):
        spb = 0.75
        over_written = ["D5:4", "C5:4"]
        over_played = ["E5:16", "D5:16", "C5:16", "D5:16", "C5:4"]
        after_written = ["D5:2", "E5:4"]
        after_played = ["D5:4.", "E5:32", "D5:32", "C5:32", "D5:32", "E5:4"]
        over_w, over_p, labels = _side_by_side(self, _decorate(snippet(_tiny("2/4", over_written)), marks={0: ["turn"]}), snippet(_tiny("2/4", over_played)))
        after_w, after_p, _ = _side_by_side(self, snippet(_tiny("3/4", after_written)), snippet(_tiny("3/4", after_played)))
        # a turn AFTER the note: Verovio draws <delayed-turn> over the note,
        # so the sign is placed here, between the note and the next one
        late = SmuflGlyph("ornamentTurn", staff_space=after_w.ss)
        late.move_to(np.array([after_w.head(0)[0] + 0.58 * (after_w.head(1)[0] - after_w.head(0)[0]), after_w.top() + 1.2 * after_w.ss, 0.0]))
        over_events, over_cues, _ = _events(over_played, spb, velocity=72, length=0.95)
        after_events, after_cues, _ = _events(after_played, spb, velocity=72, length=0.95)

        # {[1]} Checkpoint: title; the turn sign over the D, heard
        self.title()
        self.play(FadeIn(over_w), FadeIn(labels[0]), run_time=0.6)
        self.say("sign")
        self.wait(0.6)
        _perform(self, over_events, [(0.0, [over_w.note(0)]), (spb, [over_w.note(1)])])
        self.settle()

        # {[2]} Checkpoint: written out — E D C D circling the D
        self.play(FadeIn(over_p), FadeIn(labels[1]), run_time=0.6)
        circle = VGroup(*(over_p.note(i) for i in range(4)))
        self.say("circle")
        self.play(circle.animate.set_color(BLUE), run_time=0.4)
        self.wait(0.8)
        circle.set_color(INK)
        _perform(self, over_events, _lit(over_p, over_cues))
        self.settle()

        # {[3]} Checkpoint: the sign after the note — hold, then turn at the end
        self.say("after")
        self.play(FadeOut(over_w), FadeOut(over_p), FadeIn(after_w), FadeIn(late), FadeIn(after_p), run_time=0.7)
        self.play(late.animate.set_color(HIGHLIGHT), run_time=0.3)
        _perform(self, after_events, [(0.0, [after_w.note(0)]), (2 * spb, [after_w.note(1)])], tail=0.3)
        _perform(self, after_events, _lit(after_p, after_cues))
        self.settle()

        # {[4]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 4. The appoggiatura


class TheAppoggiatura(_Lesson):
    def construct(self):
        spb = 0.8
        rule1_w, rule1_p, labels = _side_by_side(
            self,
            _decorate(snippet(_tiny("2/4", ["C5:2"])), graces=[(0, "D5", False)]),
            _decorate(snippet(_tiny("2/4", ["D5:4", "C5:4"])), marks={0: ["accent"]}, slurs=[(0, 1)]),
        )
        rule2_w, rule2_p, _ = _side_by_side(
            self,
            _decorate(snippet(_tiny("3/4", ["C5:2."])), graces=[(0, "D5", False)]),
            _decorate(snippet(_tiny("3/4", ["D5:2", "C5:4"])), marks={0: ["accent"]}, slurs=[(0, 1)]),
        )
        lean = dict(velocity=56, length=1.0, per={0: dict(velocity=104)})
        events1, cues1, _ = _events(["D5:4", "C5:4"], spb, **lean)
        events2, cues2, _ = _events(["D5:2", "C5:4"], spb, **lean)

        # {[1]} Checkpoint: title; a small note before a main note, heard
        self.title()
        self.play(FadeIn(rule1_w), FadeIn(labels[0]), run_time=0.6)
        self.say("small")
        _perform(self, events1, _lit(rule1_w, cues1))
        self.settle()

        # {[2]} Checkpoint: written out — half the main note's time
        self.play(FadeIn(rule1_p), FadeIn(labels[1]), run_time=0.6)
        self.say("half")
        _perform(self, events1, _lit(rule1_p, cues1))
        self.settle()

        # {[3]} Checkpoint: stressed lean, soft resolution — the accent lit
        self.say("stress")
        _perform(self, events1, _lit(rule1_w, cues1), tail=0.3)
        _perform(self, events1, _lit(rule1_p, cues1))
        self.settle()

        # {[4]} Checkpoint: before a dotted note — two thirds
        self.say("dotted")
        self.play(FadeOut(rule1_w), FadeOut(rule1_p), FadeIn(rule2_w), FadeIn(rule2_p), run_time=0.7)
        _perform(self, events2, _lit(rule2_w, cues2), tail=0.3)
        _perform(self, events2, _lit(rule2_p, cues2))
        self.settle()

        # {[5]} Checkpoint: remember
        self.remember()


# ---------------------------------------------------------------------------
# 5. The acciaccatura


class TheAcciaccatura(_Lesson):
    def construct(self):
        spb = 0.8
        written = ["C5:4", "G4:4"]
        crushed = ["D5:32", "C5:8..", "G4:4"]
        leaning = ["D5:8", "C5:8", "G4:4"]
        acc_w, acc_p, labels = _side_by_side(
            self,
            _decorate(snippet(_tiny("2/4", written)), graces=[(0, "D5", True)]),
            snippet(_tiny("2/4", crushed)),
        )
        app_w, app_p, _ = _side_by_side(
            self,
            _decorate(snippet(_tiny("2/4", written)), graces=[(0, "D5", False)]),
            _decorate(snippet(_tiny("2/4", leaning)), marks={0: ["accent"]}, slurs=[(0, 1)]),
        )

        def tag(key):
            """The ornament's name, centred under both staves."""
            label = _bold(self.t(key), 44, HIGHLIGHT)
            return label.move_to(np.array([0.0, acc_w.bottom() - 1.25, 0.0]))

        crushed_events, crushed_cues, _ = _events(crushed, spb, velocity=100, length=0.95, per={0: dict(velocity=58)})
        leaning_events, leaning_cues, _ = _events(leaning, spb, velocity=58, length=1.0, per={0: dict(velocity=104), 2: dict(velocity=72)})

        # {[1]} Checkpoint: title; the slashed small note, heard
        self.title()
        name = tag("label-acciaccatura")
        self.play(FadeIn(acc_w), FadeIn(labels[0]), FadeIn(name), run_time=0.6)
        self.say("slash")
        _perform(self, crushed_events, _lit(acc_w, crushed_cues))
        self.settle()

        # {[2]} Checkpoint: written out — crushed in, the stress on the main note
        self.play(FadeIn(acc_p), FadeIn(labels[1]), run_time=0.6)
        self.say("crushed")
        _perform(self, crushed_events, _lit(acc_p, crushed_cues))
        self.wait(0.3)
        _perform(self, crushed_events, _lit(acc_w, crushed_cues))
        self.settle()

        # {[3]} Checkpoint: compare — the appoggiatura leans, then the acciaccatura again
        self.say("compare")
        other = tag("label-appoggiatura")
        self.play(FadeOut(acc_w), FadeOut(acc_p), FadeOut(name), FadeIn(app_w), FadeIn(app_p), FadeIn(other), run_time=0.6)
        _perform(self, leaning_events, _lit(app_w, leaning_cues), tail=0.3)
        _perform(self, leaning_events, _lit(app_p, leaning_cues), tail=0.6)
        self.play(FadeOut(app_w), FadeOut(app_p), FadeOut(other), FadeIn(acc_w), FadeIn(acc_p), FadeIn(name), run_time=0.6)
        _perform(self, crushed_events, _lit(acc_w, crushed_cues), tail=0.3)
        _perform(self, crushed_events, _lit(acc_p, crushed_cues))
        self.settle()

        # {[4]} Checkpoint: remember
        self.remember()

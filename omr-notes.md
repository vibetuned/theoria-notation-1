# MusicXML state of the Gehrkens extraction (for Pedro's review)

Extraction: `/home/flux/projects/book-extraction/output/gehrkens`
(`mxl-midi/` — MusicXML **derived from the source MIDI**, not transcribed
from the page: pitches and durations are broadly right, but notation
details are unreliable — enharmonic spelling, ties vs repeated notes,
voice assignment, grace notes/ornament signs, key signatures).

**Fix workflow**: the course reads from `assets/book/` in THIS repo — fix
the copies here and commit; the upstream extraction stays as-is. After a
fix, re-render the lesson(s) listed and rebuild module 08's exercises if
the file feeds them.

## Files used by the course (25) — the hand-fix checklist

Checked 2026-07-10 after Pedro's video review: some transcriptions are
visibly poor. Ordered by module; ⚠ marks files where MIDI-derivation is
most likely to have mangled the *notation* (spelling/ties/ornament signs),
not just the layout.

### 01-seeing-music (scene: HowNotesAreDrawn)
- [x] `fig01.musicxml` — note anatomy / stem-direction examples (ch. I).
      Stem directions and beaming ARE the content here — worth exact care.

### 02-half-steps-and-spelling (DegreeModifiers, ReadingSignatures)
- [x] ⚠ `fig18-23.musicxml` — Rice's six alteration rules (ch. III).
      Enharmonic SPELLING is the whole point; MIDI derivation loves to
      respell (D# as Eb). Highest priority.
- [x] ⚠ `fig12-13.musicxml` — the major-vs-relative-minor signature test
      (ch. III). Key signatures + final bass chords must be exact.

### 03-time (RhythmVersusMeasure)
- [x] `fig56.musicxml` — syncopation example (ch. X). Tied-note notation
      vs re-struck notes matters for the point being made.

### 04-scales-and-keys (TheMajorScaleRule, TheThreeMinors)
- [ ] `scales.musicxml` — all 15 major scales (ch. VII); lesson slices
      measures 1-2 (C major).
- [ ] ⚠ `minor.musicxml` — A minor in three forms (ch. VIII). Accidental
      spelling of the raised 6/7 must be right.

### 05-signs-and-expression (DotsTiesSlurs, LoudSoftAndTheRoadmap)
- [x] ⚠ `fig30-31.musicxml` — the tie (incl. enharmonic tie, ch. V).
      MIDI merges tied notes into one long note — the figure may have
      LOST its ties. High priority.
- [x] `fig32-33.musicxml` — the slur as phrase-mark (ch. V). Slurs are
      often absent from MIDI-derived files entirely.
- [x] `fig25-27.musicxml` — repeats / D.C. / endings (ch. IV). Repeat
      barlines and volta brackets rarely survive MIDI.

### 06-ornaments (TheOrnamentGallery, TheLeaningNotes)
All four show REALIZATIONS (written-out notes), which MIDI preserves —
but the ornament SIGNS themselves (tr, mordent, turn, grace-note shapes)
are likely gone. If the printed figures pair sign with realization, theseZ
need the sign restored by hand:
- [x] ⚠ `fig40.musicxml` — the trill (ch. VI)
- [x] ⚠ `fig45-46.musicxml` — mordent and inverted mordent
- [x] ⚠ `fig47.musicxml` — the turn
- [x] ⚠ `fig48.musicxml` — the appoggiatura (small-note shape + accent)
- [x] ⚠ `fig50-52.musicxml` — the acciaccatura (slashed stem)

### 07-intervals (HearingIntervals)
- [x] `fig62-63.musicxml` — harmonic vs melodic intervals (ch. XVII)
- [x] `fig64.musicxml` — intervals above the tonic (ch. XVII)

### 08-chords-and-cadences (TheTriadFamily, TheFourCadences)
These four ALSO feed the `cadence-naming` exercises (the drill takes the
closing two sonorities) — fixing them updates worksheets on rebuild:
- [x] `fig65.musicxml` — triads on every degree, major (ch. XVIII)
- [x] `triads.musicxml` — triads on the minor scale
- [x] `fig68.musicxml` — authentic cadence
- [x] `fig69.musicxml` — plagal cadence
- [x] `fig70.musicxml` — half-cadence (Bach)
- [x] `fig71.musicxml` — deceptive cadence (Wm. Mather)

### 09-form (FormAndStyle, PhraseToSonata)
- [ ] `fig57.musicxml` — Mozart three-voice canon (ch. XIV)
- [ ] `fig58.musicxml` — antecedent/consequent period (ch. XV)
- [ ] `beethoven.musicxml` — the Ninth's theme (ch. XV)

## Unused (no fix needed unless a lesson adopts them)

fig02-05, fig14-17, fig28, fig34-39, fig41-44, fig49, fig53, fig54-55,
fig59, fig60, fig61, fig66, fig67, fig72-79, chromatic, greatc, jasmine,
sonata, stjohn — 37 files. fig59/60/61 and fig72-79 are the likeliest
future adoptions (period continuation, thematic development, recitative,
sequence/suspension/pedal-point figures).

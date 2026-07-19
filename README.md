# theoria — Notation I (after Gehrkens)

Course content for **Notation I**, a course of the
[theoria](https://github.com/vibetuned/theoria) music-theory learning platform.
This repository is consumed as a git submodule at `courses/notation-1/` in the
main `theoria` engine repo.

The platform's true starting point — for students who cannot yet read
notes. Video-first curriculum after Gehrkens' *Music Notation and
Terminology* (A. S. Barnes, 1914; public domain): the staff and its
symbols, embellishments, scales, measure/tempo/dynamics, forms and styles,
and the chord/cadence vocabulary. Deliberately **few exercises** (scales,
forms, cadences only) — the videos carry the course.

`assets/book/` holds the book's figures as MusicXML derived from MIDI
(the extraction's `mxl-midi/`): pitches and durations are trustworthy,
notation details (enharmonics, voice assignment) less so — verify against
the page image before quoting one in a scene.

## Layout

- `course.yaml` — course manifest (module plan, book mapping)
- `assets/book/` — the book's figures (MusicXML derived from MIDI)
- `modules/NN-slug/` — one directory per module (module.yaml, content/<lang>/,
  scenes.py)

The engine, exercise generators, and tests live in the main `theoria` repo;
build outputs land in `build/` there and are never committed here.

# Replay, verify and seal: reference

`robot-reel lerobot` turns one episode of a LeRobotDataset into a folder you can open offline, attach to an issue or
hand to a colleague. It reads the dataset's own files and does not import or install the LeRobot library.

## Commands

```bash
# Export one episode (a local dataset root, or a public Hugging Face dataset id).
robot-reel lerobot SOURCE --episode N --output DIR [--revision COMMIT] [--crf 23]

# Verify an export. Standard library only: manifest, schema and the page's embedded data.
robot-reel lerobot DIR --verify
# ... also count every decoded camera frame against the episode length (needs the lerobot extra):
robot-reel lerobot DIR --verify --check-media
# ... also re-read the source dataset and compare every exported value and file hash:
robot-reel lerobot DIR --verify --check-source [--dataset PATH]

# Seal one observation inside a verified export.
robot-reel lerobot DIR --mark FRAME --signal KEY/CHANNEL [--signal ...] --note "What you saw"
```

`--check-source` on an export made from a local dataset needs `--dataset PATH`. A Hugging Face export is pinned to the
dataset's commit; a branch or tag given with `--revision` is resolved to its commit.

## What the replay shows

- **Every camera on one clock.** Each `video` feature is cut from its source file at the episode's recorded offset
  (`from_timestamp` in v3.0 files that hold many episodes) and re-encoded to H.264, so the clip holds exactly the
  episode's frames and plays in a browser. `image` features stored inside the parquet file (PNG or JPEG) are encoded
  the same way.
- **Commanded versus measured.** When `action` and `observation.state` share channel names, each joint gets a panel
  with both curves and a link to the frame with the largest recorded difference. When the names or channel counts
  differ, both are plotted separately and the page says why; the sample never guesses which channels correspond.
  Other numeric features (rewards, `next.done`, extra sensors up to 64 values per frame) are plotted on their own.
- **The language task**, episode length and frame rate, frame stepping, playback speed, keyboard control
  (arrow keys, Space, Home, End) and `#frame=N` links.
- **Provenance.** `episode.json` holds every exported value, the dataset commit (for Hugging Face sources) and the
  SHA-256 of each source file used. `manifest.json` fingerprints the page, the data and every clip.

Floating-point values are written as the shortest decimal that reads back to the same source number, so `episode.json`
can be compared with the parquet file exactly. Features the viewer cannot plot are listed under `skipped` with the
reason. Units are the dataset's own; nothing is rescaled.

## Seal one observation

`--mark` first runs `--verify`, reads each value at that frame from `episode.json`, writes `finding.json` (episode,
frame, timestamp, each `{key, name, value}`, the note, the `episode.json` hash and the tool version), adds its SHA-256
to `manifest.json`, and embeds the finding in `index.html` as one inert JSON line so the page can show it.

Rules: `FRAME` is zero-based; each `--signal` is a series key and channel name from `episode.json`, split at the last
slash; 1 to 8 distinct signals; a note of 1 to 2000 characters without control characters other than newline. A wrong
frame or channel exits with status 2 and writes nothing. `--mark` cannot be combined with `--verify`, `--output`,
`--revision`, `--episode` or `--crf`, and an export carries at most one finding (mark a copy to keep the original).

`--verify` exits with status 2 when `episode.json`, a clip or `finding.json` changed (`Hash mismatch: FILE`), when the
finding disagrees with the episode (`Finding disagrees with episode.json: FIELD`) or breaks the rules
(`Invalid finding: FIELD`), when `finding.json` exists without a manifest entry (for example after an interrupted
`--mark`), or when the finding embedded in `index.html` differs from `finding.json`.

A finding records an observation. It is not a failure label, a calibrated threshold or a signature. The hashes show the
files are unchanged since marking, not who wrote them, and a rewrite that is re-hashed and stays consistent with
`episode.json` is not detected. Check the timestamp and values printed by `--mark` against what you saw before you
hand the folder over.

**In the page.** A marked folder opens with a *Sealed finding* panel above the cameras: the note, frame, timestamp and
recorded values, and a **Go to frame N** button that works from the keyboard. The page shows the note and names as plain
text, compares the finding with its own embedded episode data, and shows an error instead of the panel if they
disagree. It does not run `--verify`, check hashes or identify the author; run `--verify` for that.
`--verify` and `--mark` print two static checks of the files: `finding_embedded` (the page carries a copy equal to
`finding.json`) and `viewer_reader_signature` (the page's script contains the finding reader's text). Neither opens a
browser, and neither proves that the panel is displayed.

## Supported datasets and limits

- LeRobotDataset **v3.0**, **v2.1** and **v2.0**. Convert v1.x datasets with LeRobot's own script first.
- One episode per export, up to 20,000 frames. Numeric features with more than 64 values per frame are skipped and listed.
- Clips are lossy H.264 viewing copies (`--crf 23` by default; lower is larger and closer to the source). The source
  videos' hashes are recorded, not their pixels.
- The replay shows what the dataset recorded. It does not judge success, calibrate units or infer contacts.

### Timeline errors

Every frame must carry `frame_index` 0..length-1 exactly once, with a finite timestamp later than the previous frame's.
A damaged episode stops the export with exit status 2 before any file is written. The message names the data file
(relative to the dataset root), the episode and the first bad value, for example `Episode 3 in
data/chunk-000/episode_000003.parquet is missing frame_index 57 ...`. The sample refuses a damaged episode; it never
reorders, fills or interpolates frames.

### Camera errors

For LeRobotDataset v3.0, a camera problem stops the export with exit status 2 and one message that starts with the
camera key and names the file relative to the dataset root. It never prints an absolute host path or a cache directory:

- `KEY: meta/episodes/... has no videos/KEY/from_timestamp for episode E; ...` The episode row lacks a `chunk_index`,
  `file_index` or `from_timestamp` for that camera. Re-run LeRobot's v3.0 conversion or remove the camera from
  `meta/info.json`. Nothing is written.
- `KEY: meta/info.json declares an image feature but DATA has no KEY column; ...` Remove the feature or re-record the
  episode with images embedded. Nothing is written.
- `KEY: cannot read camera video videos/KEY/... (CAUSE). ...` The video exists but FFmpeg cannot decode it. `CAUSE` is
  FFmpeg's last error line. The partly written output folder stays; export again into a fresh `--output` folder.

A video that is absent is reported as `Missing dataset file: videos/...` before any file is written.

### Dataset paths

The `data_path` and `video_path` templates in `meta/info.json`, filled with the chunk and file numbers from the episode
metadata, must name files inside the dataset folder. The path is resolved, which follows symlinks, so an absolute path,
a `..` part or a symlink that points out of the dataset folder stops the export (and `--check-source`) with exit status 2
before any file is written, for example `meta/info.json data_path '../other/file-000.parquet' points outside the dataset
folder; ...`. An absolute value is shown as `(an absolute path)`. Symlinks that stay inside the dataset folder work. A
folder whose files are symlinks to somewhere else (for example a Hugging Face cache snapshot) is rejected: copy it with
the links resolved (`cp -RL`) or pass the Hub dataset id instead.

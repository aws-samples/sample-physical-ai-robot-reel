# Threat model

Sample code, local use only. The tool has no server, no listening socket, no AWS API call and no credential of its own.
It reads a dataset folder (or downloads files of one public Hugging Face dataset), writes an export folder, and
re-reads an export folder. This document records what the sample protects, what it does not, and which assumptions
you inherit if you adapt it.

## Assets

| Asset | Why it matters |
|---|---|
| An export folder (`episode.json`, `manifest.json`, `cameras/*.mp4`, `index.html`, optional `finding.json`) | It is the evidence a result is judged on. |
| The machine that runs the tool | It parses files from a dataset you may not control. |
| The reader of an export page | They open a page that embeds data from a dataset and a note written by someone else. |

## Trust boundaries and inputs

1. **Dataset files** (`meta/info.json`, parquet, video): untrusted unless you made them.
2. **Hugging Face Hub responses**, when the source is a dataset id: pinned to one commit, downloaded with `huggingface_hub`.
3. **An export folder received from someone else**: untrusted until `--verify` passes, and even then only unchanged since
   it was written, not authored by a known person.
4. **Command-line arguments**: `--note` text, `--signal` names, paths.

## STRIDE

| | Threat | Mitigation in the sample | Residual risk |
|---|---|---|---|
| S | An export claims a source it did not come from. | `episode.json` records the dataset commit and the SHA-256 of each source file; `--check-source` re-reads the source and compares every value. | Hashes are not signatures. Anyone can re-export a forged folder with consistent hashes. Use signing (for example `cosign` or an Amazon S3 object lock with your own access controls) if authorship matters. |
| T | A value, clip, page or finding is changed after export. | `--verify` re-hashes every file listed in `manifest.json`, requires the page's embedded data to equal `episode.json`, and requires the embedded and stored findings to match. | A change that is re-hashed and stays self-consistent is not detected (stated in the docs and README). |
| R | A reader cannot tell who made or sealed a finding. | A finding records frame, values, note, tool version and the `episode.json` hash. | No identity is recorded by design; do not rely on it for non-repudiation. |
| I | An export leaks camera frames or paths, or a crafted dataset pulls a file from elsewhere on the machine into the export. | Messages show dataset-relative names, never absolute host or cache paths. Paths built from dataset metadata (the `data_path` and `video_path` templates in `meta/info.json`, filled with values from the episode metadata) are resolved and must stay inside the dataset root: absolute paths, `..` and symlinks that point out of the root are rejected with exit status 2 before anything is written. For a Hugging Face dataset the same names must be relative and free of `..`. The export is written only to the `--output` folder, which must be new and empty. | Camera frames can show people, places and equipment. Share exports only with people entitled to see the source dataset; a dataset keeps its own license. |
| D | A crafted dataset exhausts memory or time. | Limits: 20,000 frames per export, at most 64 values per feature per frame, at most 8 signals per finding, note up to 2,000 characters. FFmpeg gets a closed stdin. | A very large parquet file or video can still use a lot of memory and CPU. Run on data you trust, or in a container with limits. |
| E | A crafted dataset or video runs code on the machine. | The tool never executes dataset content. Subprocess calls use argument lists (no shell) with absolute paths, so no dataset or command-line text can be read as a FFmpeg option. Camera clip names are generated from a fixed pattern (`cameras/NAME.mp4` with `[\w.-]` only) and validated again in `--verify`. | Parquet parsing (`pyarrow`) and video decoding (FFmpeg) handle untrusted bytes; their vulnerabilities apply. Keep both updated. |

## The viewer page

- It is one file with an inline script and no network request. The only external links are navigation links (this
  repository's docs, and the Hugging Face dataset visualizer for pinned Hub exports).
- Dataset values and the finding are embedded as JSON with `<` escaped (`\u003c`), so they cannot close the script
  element. Notes, channel names and task text are written with `textContent`. The one `innerHTML` assignment is a constant
  string. A unit test (`tests/test_mark_and_viewer.py`) checks that there is no `eval`, `document.write`, `fetch`,
  external script or style, and no interpolation in that assignment.
- The page does not verify anything. It compares the finding with its own embedded episode data and shows an error if
  they differ. Run `--verify` for the file checks.

## Dependencies

`pyarrow`, `huggingface_hub`, `numpy` and `imageio-ffmpeg` (which supplies an FFmpeg executable) are installed only with
the `lerobot` extra. See [third-party.md](third-party.md). Pin and audit them in your own project.

## Out of scope

Authentication, encryption at rest or in transit beyond what Hugging Face and your file store provide, multi-user
access control, malware scanning of datasets, and any production hardening.

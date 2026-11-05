# Robot Reel: replay and verify one robot episode, offline

This sample turns one episode of a [LeRobotDataset](https://huggingface.co/docs/lerobot/lerobot-dataset-v3) into a
single folder that opens in a browser without a server, carries its own checksums, and can be re-checked by
anyone who holds the folder. It is sample code for learning and experimenting. It is not an AWS service, and it has
not been hardened or load-tested for production use.

Physical AI teams often report robot results as a number in a slide or a chat message. The number cannot be re-checked,
because the data behind it is not at hand. This sample shows a small, concrete way to keep the evidence next to the
claim:

- **Replay.** Every camera on one clock, commanded versus measured joints, frame stepping, keyboard control,
  shareable `#frame=N` links. The page is one HTML file plus the clips, with no network request.
- **Verify.** `episode.json` holds every exported value and the SHA-256 of each source file. `--verify` re-hashes the
  folder; `--check-source` re-reads the original dataset and compares every value.
- **Seal a finding.** `--mark` records one frame and channel you examined, with a note, inside the export. A changed
  value, note or file makes `--verify` fail.

What it does not do: it does not judge whether a run succeeded, calibrate units, or prove who wrote a file. A hash shows
that files are unchanged since they were written, not who wrote them. See [docs/threat-model.md](docs/threat-model.md).

## Architecture

```text
 LeRobotDataset (local folder, or a public Hugging Face dataset pinned to a commit)
          |  robot-reel lerobot SOURCE --episode N --output DIR      (reads parquet + video, writes files)
          v
 DIR/ index.html  episode.json  manifest.json  cameras/*.mp4   [finding.json after --mark]
          |  copy / zip / upload anywhere (for example an Amazon S3 bucket you control)
          v
 robot-reel lerobot DIR --verify [--check-media] [--check-source --dataset PATH]
```

Everything runs on your machine. There is no AWS account, service, credential or cost involved in running the sample.

## Prerequisites

- Python 3.12 or later and `pip`.
- To read a dataset (export, `--check-media`, `--check-source`): the `lerobot` extra, which installs `pyarrow`,
  `huggingface_hub`, `numpy` and `imageio-ffmpeg` (a packaged FFmpeg binary, used to cut and re-encode camera clips).
  `--verify`, `--mark` and the viewer page use only the Python standard library.

## Try it in two minutes, with synthetic data

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install ".[lerobot]"

bash examples/walkthrough.sh
```

The script writes a tiny made-up dataset (two episodes, `examples/make_synthetic_dataset.py`), exports episode 1,
verifies it, seals a finding at frame 8, then changes one value in a copy and shows `--verify` failing with
`Hash mismatch: episode.json`. Open `artifacts/walkthrough/episode1/index.html` in a browser.

## Use it on a real dataset

```bash
# A dataset on disk (for example one you recorded with LeRobot):
robot-reel lerobot ~/path/to/your_dataset --episode 3 --output artifacts/mine

# A public Hugging Face dataset; only the files this episode needs are downloaded and the export is pinned to a commit:
robot-reel lerobot some-org/some-dataset --episode 0 --output artifacts/episode0
```

Datasets keep their own licenses and are not part of this repository. Check the dataset's terms before you share an
export that contains its camera frames. Details, supported formats (LeRobotDataset v2.0, v2.1, v3.0), limits and error
messages: [docs/lerobot.md](docs/lerobot.md).

## Share an export through Amazon S3 (optional)

An export is a plain folder, so any file store works. With Amazon S3:

```bash
aws s3 sync artifacts/mine s3://amzn-s3-demo-bucket/exports/mine/        # sender
aws s3 sync s3://amzn-s3-demo-bucket/exports/mine/ received/mine/        # recipient
robot-reel lerobot received/mine --verify --check-media
```

Use a bucket you own with Block Public Access on, and grant read access only to the people who need it: camera frames
can show people, places and equipment. Replace `amzn-s3-demo-bucket` with your own bucket name. The verification does
not depend on S3; it only needs the folder.

## Accessibility

The replay page was checked with axe-core (no violations), by keyboard, and with VoiceOver on macOS. The checks, their
limits and the two gaps found earlier are in [docs/accessibility.md](docs/accessibility.md).

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests build small synthetic datasets in a temporary folder. Tests that read parquet or video are skipped when the
`lerobot` extra is not installed.

## Security

See [SECURITY.md](SECURITY.md) and [docs/threat-model.md](docs/threat-model.md). Treat datasets you did not create as
untrusted input: the sample parses parquet files and decodes video with FFmpeg.

## Third-party components

Nothing third-party is bundled. Dependencies and their licenses: [docs/third-party.md](docs/third-party.md).

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

This sample was extracted from the Robot Reel project by its author.

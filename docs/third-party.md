# Third-party components

No third-party code is bundled in this repository. The packages below are installed by `pip install ".[lerobot]"` and are not
redistributed here. Versions are those used when this sample was checked; run your own audit before you rely on them.

| Package | Version checked | License (package metadata) | Role |
|---|---|---|---|
| pyarrow | 26.0.1 | Apache-2.0 | Reads parquet files |
| huggingface_hub | 2.4.0 | Apache-2.0 | Lists and downloads files of a public dataset (Hugging Face source only) |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Array handling when reading parquet columns |
| imageio-ffmpeg | 0.8.1 | BSD-2-Clause | Supplies an FFmpeg executable, run as a separate process to cut, re-encode and count camera frames |

Transitive dependencies of `huggingface_hub` include `tqdm` (MPL-2.0 AND MIT), `fsspec` (BSD-3-Clause), `filelock` (MIT),
`PyYAML` (MIT), `packaging` (Apache-2.0 OR BSD-2-Clause), `typing_extensions` (PSF-2.0), `hf-xet` (Apache-2.0), `httpx2` and
its dependencies. Check the exact set with `pip list` and `pip-licenses` in your environment.

FFmpeg itself is licensed under the LGPL or GPL depending on how a binary was built. The binary that `imageio-ffmpeg`
provides is not part of this repository and is executed only as an external program. Read FFmpeg's license terms before
you redistribute a product that includes it.

Datasets are never bundled. A dataset keeps its own license and attribution; an export that contains its camera frames
is a derived work of that dataset.

## Dataset frames in the README demo

`docs/media/demo.gif` and `docs/media/demo.png` show camera frames and values from episode 0 of a public dataset,
exported with this sample. No dataset files or camera clips are stored in this repository.

| Dataset | Commit | License (dataset card) | Used in |
|---|---|---|---|
| [lerobot/svla_so101_pickplace](https://huggingface.co/datasets/lerobot/svla_so101_pickplace) | `f641879e22172be7e8161d5e6c1503c2d2feb657` | Apache-2.0 | Frames shown in `docs/media/demo.*` |

The frames remain under the dataset's license ([Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)).
Their use here does not imply that the dataset's authors endorse this sample.

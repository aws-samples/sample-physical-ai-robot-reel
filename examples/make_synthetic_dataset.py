"""Write a tiny synthetic LeRobotDataset (v3.0) to a folder, so the walkthrough needs no download.

    python examples/make_synthetic_dataset.py artifacts/synthetic

Two episodes (12 and 16 frames at 10 fps) share one 64x48 video; `action` and `observation.state`
have two channels, `lift` and `grip`. The values are made up. Nothing here is real robot data.
Needs the `lerobot` extra: pip install ".[lerobot]"
"""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import pyarrow as pa
import pyarrow.parquet as pq

FPS = 10
LENGTHS = (12, 16)
KEY = "observation.images.top"


def level(index):
    return 20 + 10 * index  # gray level that identifies a frame after lossy coding


def frames(episode, start):
    count = LENGTHS[episode]
    lift = [0.1 * i for i in range(count)]
    return pa.table({
        "action": pa.array([[lift[i] + 0.3, -0.5] for i in range(count)], pa.list_(pa.float32(), 2)),
        "observation.state": pa.array([[lift[i], -0.5 + 0.01 * i] for i in range(count)], pa.list_(pa.float32(), 2)),
        "next.done": [i == count - 1 for i in range(count)],
        "timestamp": pa.array([i / FPS for i in range(count)], pa.float32()),
        "frame_index": list(range(count)), "episode_index": [episode] * count,
        "index": list(range(start, start + count)), "task_index": [0] * count,
    })


def write_video(path, total):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(bytes([level(i) % 256]) * (64 * 48 * 3) for i in range(total))
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                    "-s", "64x48", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(path)], input=raw, check=True)


def main(target):
    root = Path(target)
    if root.exists() and any(root.iterdir()):
        sys.exit(f"{root} is not empty; choose a fresh folder")
    (root / "meta/episodes/chunk-000").mkdir(parents=True)
    (root / "data/chunk-000").mkdir(parents=True)
    motors = {"dtype": "float32", "shape": [2], "names": {"motors": ["lift", "grip"]}}
    one = {"dtype": "int64", "shape": [1]}
    info = {"codebase_version": "v3.0", "robot_type": "synthetic", "fps": FPS, "chunks_size": 1000,
            "total_episodes": 2,
            "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
            "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
            "features": {KEY: {"dtype": "video", "shape": [48, 64, 3]}, "action": motors, "observation.state": motors,
                         "next.done": {"dtype": "bool", "shape": [1]}, "timestamp": {"dtype": "float32", "shape": [1]},
                         "frame_index": one, "episode_index": one, "index": one, "task_index": one}}
    (root / "meta/info.json").write_text(json.dumps(info, indent=1))
    pq.write_table(pa.concat_tables([frames(0, 0), frames(1, LENGTHS[0])]), root / "data/chunk-000/file-000.parquet")
    write_video(root / f"videos/{KEY}/chunk-000/file-000.mp4", sum(LENGTHS))
    pq.write_table(pa.table({
        "episode_index": [0, 1], "data/chunk_index": [0, 0], "data/file_index": [0, 0],
        f"videos/{KEY}/chunk_index": [0, 0], f"videos/{KEY}/file_index": [0, 0],
        f"videos/{KEY}/from_timestamp": [0.0, LENGTHS[0] / FPS],
        f"videos/{KEY}/to_timestamp": [LENGTHS[0] / FPS, sum(LENGTHS) / FPS],
        "tasks": [["lift the block"], ["lift the block"]], "length": list(LENGTHS),
    }), root / "meta/episodes/chunk-000/file-000.parquet")
    print(f"Wrote {root} (2 episodes, {sum(LENGTHS)} frames)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "artifacts/synthetic")

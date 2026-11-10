"""Paths from dataset metadata must stay inside the dataset folder.

meta/info.json data_path and video_path templates, filled with values from the episode metadata, are
dataset input. A value that leaves the dataset root ('..', an absolute path, or a symlink out of the root)
is rejected with exit status 2 before anything is written. Every dataset here is a small synthetic fixture
built in a temporary directory, next to a copy of its files outside the dataset.
"""
import json
from pathlib import Path
import shutil
import unittest

from robot_reel.lerobot import Source
import test_camera_errors as camera
from test_camera_errors import DATA, HAS_READER, TOP, VIDEO


@unittest.skipUnless(HAS_READER, "Install the lerobot extra (pip install '.[lerobot]') to read parquet datasets")
class DatasetPathTest(unittest.TestCase):
    # The same synthetic v3.0 dataset and CLI helpers as the camera error tests.
    # (Imported through the module, so the camera tests are not collected twice.)
    setUp, build, cli, failed_export = (camera.CameraErrorTest.setUp, camera.CameraErrorTest.build,
                                        camera.CameraErrorTest.cli, camera.CameraErrorTest.failed_export)

    def outside(self, name):
        """Copy a dataset file to a folder beside the dataset; return the copy."""
        target = Path(self.temporary)/"outside"/Path(name).name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(self.root/name, target)
        return target

    def set_info(self, **changes):
        path = self.root/"meta/info.json"
        info = json.loads(path.read_text())
        info.update(changes)
        path.write_text(json.dumps(info))

    def rejected(self, field, shown):
        message = self.failed_export()
        self.assertIn(f"{field} {shown} points outside the dataset folder", message)
        self.assertFalse(self.output.exists())
        return message

    def test_data_path_with_parent_parts_is_rejected(self):
        self.outside(DATA)
        self.set_info(data_path="../outside/file-{file_index:03d}.parquet")
        self.rejected("meta/info.json data_path", "'../outside/file-000.parquet'")

    def test_video_path_with_parent_parts_is_rejected(self):
        self.outside(VIDEO)
        self.set_info(video_path="../outside/file-{file_index:03d}.mp4")
        self.rejected(f"{TOP}: meta/info.json video_path", "'../outside/file-000.mp4'")

    def test_absolute_template_path_is_rejected_and_not_shown(self):
        copy = self.outside(DATA)
        self.set_info(data_path=str(copy.resolve()))
        message = self.rejected("meta/info.json data_path", "(an absolute path)")
        self.assertNotIn(str(copy), message)

    def test_symlink_out_of_the_dataset_is_rejected(self):
        copy = self.outside(DATA)
        (self.root/DATA).unlink()
        (self.root/DATA).symlink_to(copy)
        self.rejected("meta/info.json data_path", repr(DATA))

    def test_symlinked_video_folder_out_of_the_dataset_is_rejected(self):
        folder = Path(self.temporary)/"outside-videos"
        shutil.move(self.root/"videos", folder)
        (self.root/"videos").symlink_to(folder, target_is_directory=True)
        self.rejected(f"{TOP}: meta/info.json video_path", repr(VIDEO))

    def test_symlink_inside_the_dataset_still_exports(self):
        moved = self.root/"data/chunk-000/real.parquet"
        (self.root/DATA).rename(moved)
        (self.root/DATA).symlink_to(moved.name)
        for args in ([self.root, "--episode", "0", "--output", self.output],
                     [self.output, "--verify", "--check-media", "--check-source", "--dataset", self.root]):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_normal_dataset_exports_and_verifies_as_before(self):
        for args in ([self.root, "--episode", "0", "--output", self.output],
                     [self.output, "--verify", "--check-media", "--check-source", "--dataset", self.root]):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads((self.output/"episode.json").read_text())
        self.assertEqual(sorted(trace["source_files"]), sorted({"meta/info.json", DATA, VIDEO}))
        self.assertEqual(trace["cameras"][0]["source"], VIDEO)
        self.assertEqual(sorted(json.loads((self.output/"manifest.json").read_text())["sha256"]),
                         ["cameras/top.mp4", "episode.json", "index.html"])


class HubPathTest(unittest.TestCase):
    """A Hub dataset has no local root: names are checked before huggingface_hub is asked for them."""

    def hub(self):
        source = Source.__new__(Source)
        source.root, source.repo_id, source.revision = None, "some-org/some-dataset", "0"*40
        return source

    def test_parent_parts_and_absolute_names_are_rejected(self):
        for name, shown in (("../x.parquet", "'../x.parquet'"), ("data/../../x.mp4", "'data/../../x.mp4'"),
                            ("/etc/x.parquet", "(an absolute path)")):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "points outside the dataset folder") as caught:
                self.hub().contain(name, "meta/info.json data_path")
            self.assertIn(f"meta/info.json data_path {shown}", str(caught.exception))

    def test_relative_names_pass(self):
        self.assertEqual(self.hub().contain(DATA), DATA)


if __name__ == "__main__":
    unittest.main()

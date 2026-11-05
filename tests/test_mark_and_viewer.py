"""Sealing a finding, tampering, and the accessibility contract of the viewer page."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from robot_reel.lerobot import export, main, mark, verify

ROOT = Path(__file__).resolve().parents[1]
HAS_READER = all(importlib.util.find_spec(m) for m in ("pyarrow", "numpy", "imageio_ffmpeg", "huggingface_hub"))
TEMPLATE = (ROOT/"robot_reel/lerobot.html").read_text()


def synthetic_dataset(target):
    spec = importlib.util.spec_from_file_location("make_synthetic_dataset", ROOT/"examples/make_synthetic_dataset.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with contextlib.redirect_stdout(io.StringIO()):
        module.main(str(target))


@unittest.skipUnless(HAS_READER, "Install the lerobot extra (pip install '.[lerobot]') to read parquet datasets")
class SealedFindingTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        synthetic_dataset(self.base/"dataset")
        export(self.base/"dataset", 1, self.base/"episode")
        self.folder = self.base/"episode"

    def test_mark_is_recorded_embedded_and_verified(self):
        result = mark(self.folder, 8, ["observation.state/lift"], "Lift passes 0.8 here")
        self.assertTrue(result["finding_embedded"])
        self.assertTrue(result["viewer_reader_signature"])
        checked = verify(self.folder)
        self.assertEqual(checked["finding"]["note"], "Lift passes 0.8 here")
        self.assertEqual(checked["finding"]["signals"][0]["key"], "observation.state")
        self.assertAlmostEqual(checked["finding"]["signals"][0]["value"], 0.8, places=5)

    def test_changed_value_note_or_second_finding_is_rejected(self):
        mark(self.folder, 8, ["observation.state/lift"], "first")
        with self.assertRaisesRegex(ValueError, "already holds a finding"):
            mark(self.folder, 8, ["observation.state/lift"], "second")
        finding = self.folder/"finding.json"
        original = finding.read_text()
        finding.write_text(original.replace("first", "other"))
        with self.assertRaisesRegex(ValueError, "Hash mismatch: finding.json"):
            verify(self.folder)
        finding.write_text(original)
        episode = self.folder/"episode.json"
        trace = json.loads(episode.read_text())
        trace["series"][0]["values"][3][0] += 1
        episode.write_text(json.dumps(trace, indent=1)+"\n")
        with self.assertRaisesRegex(ValueError, "Hash mismatch: episode.json"):
            verify(self.folder)

    def test_wrong_frame_or_channel_writes_nothing(self):
        before = sorted(p.name for p in self.folder.iterdir())
        with self.assertRaises(ValueError):
            mark(self.folder, 999, ["observation.state/lift"], "x")
        with self.assertRaises(ValueError):
            mark(self.folder, 3, ["observation.state/nope"], "x")
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), before)

    def test_cli_verify_exit_status_on_a_damaged_export(self):
        (self.folder/"index.html").write_text("<html></html>")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            main([str(self.folder), "--verify"])
        self.assertEqual(raised.exception.code, 2)


class ViewerContractTest(unittest.TestCase):
    """Static checks of the template. The browser behaviour was checked by hand; see docs/accessibility.md."""

    def test_slider_has_a_unit_and_buttons_announce_the_frame(self):
        self.assertIn("setAttribute('aria-valuetext'", TEMPLATE)
        self.assertRegex(TEMPLATE, r"function step\(delta\)\{seek\(current\+delta\);\$\('status'\)\.textContent=")
        self.assertIn('<p id="status" role="status">', TEMPLATE)
        self.assertIn('aria-label="Previous frame"', TEMPLATE)
        self.assertIn('aria-label="Next frame"', TEMPLATE)
        self.assertIn('<html lang="en">', TEMPLATE)

    def test_page_loads_nothing_from_the_network_and_writes_no_untrusted_html(self):
        urls = set(re.findall(r"https?://[^\"'<>) ]+", TEMPLATE))
        self.assertEqual({u.split("?")[0] for u in urls}, {
            "https://github.com/aws-samples/sample-physical-ai-robot-reel",
            "https://github.com/aws-samples/sample-physical-ai-robot-reel/blob/main/docs/lerobot.md",
            "https://huggingface.co/spaces/lerobot/visualize_dataset"})
        for forbidden in ("<script src", "<link rel=\"stylesheet\"", "fetch(", "XMLHttpRequest", "eval(", "new Function",
                          "document.write", "insertAdjacentHTML", "outerHTML"):
            self.assertNotIn(forbidden, TEMPLATE)
        # The only innerHTML assignment is a constant string.
        assigned = re.findall(r"innerHTML\s*=\s*([^;]+);", TEMPLATE)
        self.assertEqual(len(assigned), 1)
        self.assertNotIn("${", assigned[0])


if __name__ == "__main__":
    unittest.main()

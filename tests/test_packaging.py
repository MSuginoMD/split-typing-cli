import unittest
import tomllib
from pathlib import Path


class TestPackaging(unittest.TestCase):
    def test_pyproject_has_entrypoint_and_dep(self):
        data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("split-typing", data["project"]["scripts"])
        self.assertTrue(any("pykakasi" in d for d in data["project"]["dependencies"]))

    def test_license_exists(self):
        self.assertTrue(Path("LICENSE").exists())

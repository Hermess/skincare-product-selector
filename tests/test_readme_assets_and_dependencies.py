#!/usr/bin/env python3
import json
import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class ReadmeAssetsAndDependenciesTest(unittest.TestCase):
    def test_readme_images_exist_and_are_audited(self):
        readme = (SKILL_DIR / "README.md").read_text(encoding="utf-8")
        audit = (SKILL_DIR / "assets" / "IMAGE_AUDIT.md").read_text(encoding="utf-8")
        image_paths = re.findall(r"!\[[^\]]+\]\((assets/[^)]+\.svg)\)", readme)

        self.assertGreaterEqual(len(image_paths), 3)
        for image_path in image_paths:
            self.assertTrue((SKILL_DIR / image_path).exists(), image_path)
            self.assertIn(Path(image_path).name, audit)
        self.assertIn("Approved", audit)

    def test_dependency_manifest_lists_recommended_plugins(self):
        manifest = json.loads((SKILL_DIR / "dependencies.json").read_text(encoding="utf-8"))
        plugin_names = {plugin["name"] for plugin in manifest["plugins"]}

        for expected in {"Browser", "Chrome", "Computer Use"}:
            self.assertIn(expected, plugin_names)


if __name__ == "__main__":
    unittest.main()

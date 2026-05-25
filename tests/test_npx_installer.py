#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class NpxInstallerTest(unittest.TestCase):
    def test_package_has_single_bin(self):
        package = json.loads((SKILL_DIR / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(package["bin"]["skincare-product-selector"], "bin/skincare-product-selector.js")

    def test_docs_show_npx_install_and_do_not_mention_superpowers(self):
        readme = (SKILL_DIR / "README.md").read_text(encoding="utf-8")
        install = (SKILL_DIR / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("npx -y github:Hermess/skincare-product-selector install", readme)
        self.assertIn("npx -y github:Hermess/skincare-product-selector install", install)
        self.assertIn("Browser", readme)
        self.assertIn("Browser", install)

    def test_installer_copies_skill_to_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skincare-product-selector"
            result = subprocess.run(
                ["node", "bin/skincare-product-selector.js", "install", "--target", str(target)],
                cwd=SKILL_DIR,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "tools" / "source_probe.py").exists())
            self.assertFalse((target / ".git").exists())


if __name__ == "__main__":
    unittest.main()

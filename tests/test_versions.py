import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class VersionAgreementTest(unittest.TestCase):
    def test_versions_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
        self.assertIsNotNone(m, "no '## [x.y.z]' entry in CHANGELOG.md")
        self.assertEqual(plugin["version"], market["plugins"][0]["version"])
        self.assertEqual(plugin["version"], m.group(1))


if __name__ == "__main__":
    unittest.main()

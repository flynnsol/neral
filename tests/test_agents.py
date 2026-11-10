import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("name", "description", "tools", "model")


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing leading '---'")
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    raise ValueError("missing closing '---'")


class AgentFrontmatterTest(unittest.TestCase):
    def test_agent_files(self):
        for path in sorted((ROOT / "agents").glob("*.md")):
            with self.subTest(agent=path.name):
                fm = parse_frontmatter(path.read_text(encoding="utf-8"))
                for key in REQUIRED:
                    self.assertTrue(fm.get(key), f"{path.name}: empty or missing '{key}'")
                self.assertEqual(fm["name"], path.stem)


if __name__ == "__main__":
    unittest.main()

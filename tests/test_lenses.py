import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAINTAINABILITY = ROOT / "lenses" / "maintainability.md"

OVER_BUILT_CHECKS = {
    "unrequested options": ("unrequested", "option"),
    "one-caller wrappers": ("wrapper", "one caller"),
    "code for later": ("for later",),
    "new dependency for a few lines": ("new dependency",),
    "reimplemented standard library": ("standard library", "existing helper"),
}
NEVER_CUT = ("validation", "data-loss", "security", "accessibility")


def section(text, heading):
    match = re.search(
        rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S
    )
    if not match:
        raise ValueError(f"missing section '## {heading}'")
    return match.group(1).lower()


class MaintainabilityLensTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = MAINTAINABILITY.read_text(encoding="utf-8")
        cls.look_for = section(text, "Look for")
        cls.ignore = section(text, "Ignore")

    def test_look_for_over_built_code(self):
        self.assertIn("over-built", self.look_for)
        for name, terms in OVER_BUILT_CHECKS.items():
            for term in terms:
                with self.subTest(check=name, term=term):
                    self.assertIn(term, self.look_for)

    def test_ignore_deliberate_shortcuts(self):
        self.assertIn("deliberate", self.ignore)

    def test_never_cut_items_not_flagged_as_over_built(self):
        line = next(
            (l for l in self.ignore.splitlines() if "over-built" in l), None
        )
        self.assertIsNotNone(line, "no Ignore bullet about over-built code")
        self.assertIn("never", line)
        for item in NEVER_CUT:
            with self.subTest(item=item):
                self.assertIn(item, line)


if __name__ == "__main__":
    unittest.main()

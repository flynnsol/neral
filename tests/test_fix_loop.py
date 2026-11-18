import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX_LOOP = ROOT / "skills" / "review" / "fix-loop.md"

STEP4_PHRASES = {
    "worktree_remove": "git worktree remove <path>",
    "branch_delete": "git branch -d <branch>",
    "after_clean_merge": "after each engineer branch merges cleanly",
    "keep_on_failure": "if the merge fails or the engineer escalated, keep the worktree and report its path",
    "separate_commands": "run git as separate commands",
}


def step4(text):
    match = re.search(r"^4\. (.*)$", text, re.MULTILINE)
    if not match:
        raise ValueError("step 4 not found")
    return match.group(1)


class FixLoopWorktreeCleanupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = step4(FIX_LOOP.read_text(encoding="utf-8"))
        cls.step = " ".join(cls.raw.lower().split())

    def test_step4_is_merge_step(self):
        self.assertIn("merge the engineer commits into the working branch", self.step)

    def test_phrases(self):
        for key, phrase in STEP4_PHRASES.items():
            with self.subTest(key=key):
                self.assertIn(phrase, self.step)

    def test_never_force_delete(self):
        self.assertNotIn("-D", self.raw)


if __name__ == "__main__":
    unittest.main()

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_build import validate


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.repository = "example/source"
        self.commit = "a" * 40
        self.run = dict(
            id=123,
            repository=dict(full_name=self.repository),
            head_repository=dict(full_name=self.repository),
            path=".github/workflows/sketch-tools.yml",
            event="workflow_dispatch",
            status="completed",
            conclusion="success",
            head_sha=self.commit,
        )

    def test_selects_source_commit_independently_of_downloads_repo_commit(self):
        self.assertEqual(
            validate(self.run, self.repository, self.commit),
            dict(repository=self.repository, commit=self.commit, run=123),
        )

    def test_rejects_fork_wrong_commit_failed_and_unfinished_builds(self):
        for key, value in (
            ("head_repository", dict(full_name="someone/fork")),
            ("head_sha", "b" * 40),
            ("conclusion", "failure"),
            ("status", "in_progress"),
            ("event", "pull_request"),
            ("path", ".github/workflows/other.yml"),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.run)
                changed[key] = value
                with self.assertRaises(ValueError):
                    validate(changed, self.repository, self.commit)


if __name__ == "__main__":
    unittest.main()

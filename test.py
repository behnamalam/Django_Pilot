"""Small non-GUI smoke tests for Django Pilot helpers."""
import os
import tempfile
import unittest
from pathlib import Path

from commands import find_project_root, venv_python


class ProjectHelperTests(unittest.TestCase):
    def test_find_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sample"
            nested = root / "app" / "module"
            nested.mkdir(parents=True)
            (root / "manage.py").write_text("# Django entry point\n", encoding="utf-8")
            self.assertEqual(find_project_root(nested), root.resolve())

    def test_find_project_root_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(find_project_root(tmp))

    def test_venv_python_path_shape(self):
        path = venv_python("/workspace/.venv")
        if os.name == "nt":
            self.assertEqual(path.name, "python.exe")
            self.assertEqual(path.parent.name, "Scripts")
        else:
            self.assertEqual(path.name, "python")
            self.assertEqual(path.parent.name, "bin")


if __name__ == "__main__":
    unittest.main()

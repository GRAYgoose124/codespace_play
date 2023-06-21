from pathlib import Path
import shutil
import pytest

from dizzy.daemon.gen import generate_data_dir, generate_skeleton_task


class TestGen:
    def setup_method(self):
        self.test_path = Path("./tests/output/demo")

    def teardown_method(self):
        pass
        # shutil.rmtree(self.test_path)

    def test_generate_data_dir(self):
        generate_data_dir(self.test_path, demo=True)

        assert (self.test_path / "data" / "common_services").exists()

    def test_is_task_import_working(self):
        generate_skeleton_task("task_name", "groupfile", self.test_path, [], [], [])
        file = self.test_path / "groupfile.py"
        if "from dizzy import Task" in file.read_text():
            assert True

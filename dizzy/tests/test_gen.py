from pathlib import Path
import shutil
import pytest
import time

from dizzy.daemon.gen import generate_data_dir, generate_skeleton_task


class TestGen:
    @classmethod
    def setup_class(cls):
        cls.test_path = Path("./tests/output/demo")

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.test_path)

    def test_generate_data_dir(self):
        generate_data_dir(self.test_path, demo=True)

        assert (self.test_path / "data" / "common_services").exists()

    # @pytest.mark.skip(reason="Not implemented yet")
    def test_is_task_import_working(self):
        generate_skeleton_task("task_name", "groupfile", self.test_path, [], [], [])
        file = self.test_path / "groupfile.py"
        if "from dizzy import Task" in file.read_text():
            assert True
        else:
            assert False

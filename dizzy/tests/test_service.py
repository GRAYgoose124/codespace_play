import pytest
from pathlib import Path

from dizzy import ServiceManager, Service
from dizzy.daemon.settings import common_services


class TestServiceManager:
    def setup_method(self):
        self.man = ServiceManager()
        self.man.load_services(common_services.values())

        print(common_services, self.man.services.values())

    def test_ServiceManager(self):
        assert self.man.get_service("uno").get_task("D").run({}) == "D"

    def test_task_resolution(self):
        assert [t.name for t in self.man.resolve_task_dependencies("D")] == ["D"]

    def test_task_resolution_with_dependencies(self):
        assert [t.name for t in self.man.resolve_task_dependencies("C")] == [
            "A",
            "B",
            "C",
        ]

    def test_run_tasklist(self):
        ctx = {}
        tasklist = self.man.resolve_task_dependencies("C")
        self.man.run_tasklist(tasklist, ctx)
        assert ctx == {"A": "A", "B": "AB", "C": "C"}


class TestService:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.service = Service.load_from_yaml(common_services["uno"])

    def teardown_method(self):
        self.test_path.unlink()

    def test_Service_dump(self):
        self.service.save_to_yaml(self.test_path)

        test_S = Service.load_from_yaml(self.test_path)
        assert self.test_path.exists()
        assert test_S.name == "uno"
        assert not hasattr(test_S, "__task_root")

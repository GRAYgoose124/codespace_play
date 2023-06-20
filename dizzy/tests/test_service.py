import pytest
from pathlib import Path

from dizzy import ServiceManager
from dizzy.daemon.settings import default_services


class TestServiceManager:
    def setup_method(self):
        self.man = ServiceManager()
        self.man.load_services(default_services)

    def test_ServiceManager(self):
        assert self.man.services["uno"].get_task("D").run({}) == "D"

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
        assert ctx == {"A": "A", "B": "B", "C": "C"}

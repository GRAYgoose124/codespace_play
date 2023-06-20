import pytest
from pathlib import Path

from dizzy import ServiceManager
from dizzy.daemon.settings import default_services


class TestServiceManager:
    def setup(self):
        self.man = ServiceManager()
        self.man.load_services(default_services)

    def test_ServiceManager(self):
        assert self.man.services["uno"].get_task("D").run() == "D"

    @pytest.mark.skip
    def test_task_resolution(self):
        self.man.resolve_task_dependencies("D")

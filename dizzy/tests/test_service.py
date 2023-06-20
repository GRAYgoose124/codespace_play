import pytest
from pathlib import Path

from dizzy import ServiceManager


class TestServiceManager:
    def test_ServiceManager(self):
        root = Path(__file__).parent.parent / "dizzy"
        uno_file = root / "simple_service/uno.yml"

        services = [uno_file]

        man = ServiceManager()

        man.load_services(services)

        assert man.services["uno"].get_task("D").run() == "D"

import json
import pytest

from pathlib import Path

from dere.services import ServiceManager, Service


def create_test_service(label: str) -> Service:
    # create the module file
    with open(f"{label}.py", "w") as f:
        f.write(f"def {label}():\n    print('Hello World!')\n")

    return Service(
        name=f"{label}",
        description="A test service.",
        module_path=f"{label}.py",
        import_path=label,
    )


class TestServiceManager:
    def setup_method(self):
        self.man = ServiceManager()

        for i in range(1, 4):
            self.man.add_service(create_test_service(f"service_{i}"))

    def teardown_method(self):
        # remove the module files
        for i in range(1, 4):
            Path(f"service_{i}.py").unlink()

    def test_gettersetters(self):
        assert self.man.get_service("service_1").name == "service_1"

        self.man.remove_service("service_1")
        with pytest.raises(KeyError):
            assert self.man.get_service("service_1")

        self.man.add_service(create_test_service("service_1"))

        services = self.man.get_services()
        assert all(
            [s.name in ["service_1", "service_2", "service_3"] for s in services]
        )

    def test_schema(self):
        path = "test.yml"
        self.man.save(path)

        man_from_schema = ServiceManager.load(path)

        service_from_json = man_from_schema.get_service("service_1")
        assert service_from_json.name == "service_1"
        assert service_from_json.description == "A test service."
        assert service_from_json.module_path == "service_1.py"
        assert service_from_json.import_path == "service_1"

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import yaml
import importlib


def load_module(path: Path) -> object:
    """Load a module from a path."""
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@dataclass
class Task(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, *args, **kwargs):
        pass


@dataclass
class Service:
    name: str
    description: str

    tasks: list[str] = field(default_factory=list)
    dependencies: list[list[str, list[str]]] = field(default_factory=list)

    def __post_init__(self):
        self.__task_root = None
        self.__loaded_tasks = {}

    def _load_tasks(self):
        print(self.__task_root)
        # find all py in task_root and check if they are in tasks
        for task in Path(self.__task_root).glob("*.py"):
            # load module and find any class that inherits from Task
            module = load_module(task)
            print(task, module.__dict__.keys())
            for name, obj in module.__dict__.items():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, Task)
                    and name in self.tasks
                ):
                    self.__loaded_tasks[name] = obj

    @staticmethod
    def load_from_yaml(service: Path) -> "Service":
        with open(service) as f:
            S = Service(**yaml.safe_load(f)["service"])
            S.__task_root = str(service.parent)
            S._load_tasks()

            return S

    def get_task(self, name: str) -> Task:
        if name not in self.__loaded_tasks:
            if name in self.tasks:
                raise ValueError(f"Task {name} not loaded")
            raise KeyError(f"Task {name} not found in service {self.name}")
        return self.__loaded_tasks[name]


class ServiceManager:
    def __init__(self):
        self.services = {}

    def load_services(self, services: list[Path]):
        for service in services:
            S = Service.load_from_yaml(service)
            self.services[S.name] = S


def main():
    root = Path(__file__).parent
    uno_file = root / "simple_service/uno.yml"

    services = [uno_file]

    man = ServiceManager()

    man.load_services(services)

    print(man.services["uno"].get_task("D").run())


if __name__ == "__main__":
    main()

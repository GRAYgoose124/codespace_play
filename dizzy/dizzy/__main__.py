from abc import ABC, abstractmethod
import asyncio
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
    # dependencies: list[str] = field(default_factory=list)

    @abstractmethod
    def run(self, *args, **kwargs):
        pass


@dataclass
class Service:
    name: str
    description: str

    tasks: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.__task_root = None
        self.__loaded_tasks = {}

    def _load_tasks(self):
        for task in Path(self.__task_root).glob("*.py"):
            module = load_module(task)
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
            S.__task_root = str(service.parent / "tasks")
            S._load_tasks()

            return S

    def get_task(self, name: str) -> Task:
        if name not in self.__loaded_tasks:
            if name in self.tasks:
                raise ValueError(f"Task {name} not loaded")
            raise KeyError(f"Task {name} not found in service {self.name}")
        return self.__loaded_tasks[name]

    def get_tasks(self) -> list[Task]:
        return list(self.__loaded_tasks.values())


class ServiceManager:
    def __init__(self):
        self.services = {}

    def load_services(self, services: list[Path]):
        for service in services:
            S = Service.load_from_yaml(service)
            self.services[S.name] = S


class SimpleCLIClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def run(self):
        while True:
            service = input("Service: ")
            task = input("Task: ")

            self.socket.send(json.dumps({"service": service, "task": task}).encode())

            message = self.socket.recv()

            print(message)


def main():
    # root = Path(__file__).parent
    # uno_file = root / "simple_service/uno.yml"

    # services = [uno_file]

    # man = ServiceManager()

    # man.load_services(services)

    # print(man.services["uno"].get_task("D").run())

    # run server in background
    asyncio.run(RequestServer().run())

    SimpleCLIClient().run()


if __name__ == "__main__":
    main()

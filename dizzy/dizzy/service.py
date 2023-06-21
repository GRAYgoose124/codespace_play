from pathlib import Path
from typing import Optional

import yaml
import importlib
import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


def load_module(path: Path) -> object:
    """Load a module from a path."""
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@dataclass
class Task(ABC):
    name: Optional[str] = None
    description: Optional[str] = None
    dependencies: Optional[list[str]] = field(default_factory=list)

    def __post_init__(self):
        if self.name is None:
            self.name = self.__class__.__name__

        if self.description is None:
            self.description = self.__class__.__doc__

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
                    logger.debug(f"[{self.name}] Loading task {name} from {task}")
                    obj.name = obj.__name__
                    obj.description = obj.__doc__
                    self.__loaded_tasks[name] = obj

    @staticmethod
    def load_from_yaml(service: Path) -> "Service":
        with open(service) as f:
            logger.debug(f"Loading service from {service}")
            S = Service(**yaml.safe_load(f)["service"])
            S.__task_root = str(service.parent / "tasks")
            S._load_tasks()

            logger.debug(f"Loaded service {S.name} with tasks {S.tasks}")
            return S

    def get_task(self, name: str) -> Task:
        if name not in self.__loaded_tasks:
            if name in self.tasks:
                raise ValueError(f"Task {name} not loaded")
            raise KeyError(f"Task {name} not found in service {self.name}")
        return self.__loaded_tasks[name]

    def get_tasks(self) -> list[Task]:
        return list(self.__loaded_tasks.values())

    def get_task_names(self) -> list[str]:
        return list(self.__loaded_tasks.keys())


class ServiceManager:
    def __init__(self):
        self.services = {}
        logger.debug(f"Created new service manager {self}")

    def load_services(self, services: list[Path]):
        for service in services:
            S = Service.load_from_yaml(service)
            self.services[S.name] = S
            logger.debug(f"Loaded service {S.name}")

    def find_owner_service(self, task: str) -> Optional[Service]:
        for service in self.services.values():
            if task in service.tasks:
                return service
        return None

    def get_service(self, service: str) -> Optional[Service]:
        if service in self.services:
            return self.services[service]
        return None

    def get_services(self) -> list[Service]:
        return list(self.services.values())

    def get_service_names(self) -> list[str]:
        return list(self.services.keys())

    def get_service_items(self) -> list[tuple[str, list[str]]]:
        return [(s.name, s.get_task_names()) for s in self.services.values()]

    def find_task(self, task: str) -> Optional[Task]:
        owner = self.find_owner_service(task)
        if owner:
            return owner.get_task(task)
        return None

    def resolve_task_dependencies(self, task: str) -> list[Task]:
        """Turn a task into a list of tasks, with dependencies first"""
        t = self.find_task(task)

        if not t or t is None:
            raise ValueError(f"Task {task} not found")

        tasks = []

        if "dependencies" not in t.__dict__ or not t.dependencies:
            return [t]

        for dep in t.dependencies:
            tasks = self.resolve_task_dependencies(dep) + tasks
        tasks.append(t)

        return tasks

    def run_tasklist(self, tasklist: list[Task], ctx: dict) -> dict:
        """Run a tasklist in a context"""
        logger.debug(f"Running {tasklist=}")

        results = []
        for task in tasklist:
            logger.debug(f"-- Running task {task.name}, {ctx=}")
            results.append(task.run(ctx))

        logger.debug(f"- Tasklist results: {results=}")
        return results[-1] if len(results) > 0 else None

    def run_task(self, task: str, ctx: dict) -> dict:
        """Run a task in a context"""
        logger.debug(f"Running {task=}")

        tasklist = self.resolve_task_dependencies(task)
        return self.run_tasklist(tasklist, ctx)

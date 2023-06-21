from dataclasses import dataclass, asdict
import logging
from pathlib import Path
from typing import Optional

import yaml

from . import ServiceManager

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Base class for all entities.

    An entity is... A decoupled set of services and workflows that can be deployed.
    """

    name: str
    description: str
    services: list[str]
    workflows: list[str]

    def __post_init__(self):
        self.__services_root = None
        self.__service_manager = None

    @staticmethod
    def load_from_yaml(entity: Path) -> "Entity":
        with open(entity) as f:
            logger.debug(f"Loading entity from {entity}")
            E = Entity(**yaml.safe_load(f)["entity"])
            E.__services_root = entity.parent / "services"

            E.service_manager.load_services(E.get_service_files())
            logger.debug(f"Loaded entity {E.name}")
            return E

    def save_to_yaml(self, entity: Path = None):
        if entity is None:
            if self.__services_root is None:
                raise ValueError("No services root set, cannot save entity.")
            entity = self.__services_root.parent / "entity.yml"
        else:
            self.__services_root = entity.parent / "services"

        with open(entity, "w") as f:
            yaml.safe_dump({"entity": asdict(self)}, f)

    @property
    def service_manager(self) -> ServiceManager:
        if self.__service_manager is None:
            self.__service_manager = ServiceManager()
        return self.__service_manager

    def get_service_files(self) -> list[Path]:
        if self.__services_root is None:
            raise ValueError("No services root set")

        service_files = self.__services_root.glob(f"**/*.yml")
        service_files = [f for f in service_files if f.parent.name in self.services]

        logger.debug(
            f"Found {self.name} service files {service_files} in {self.__services_root}"
        )

        return service_files

    def run_workflow(self, workflow: str):
        """A workflow is a set of non-dependent tasks made dependent by the workflow."""
        logger.debug(f"Running workflow {workflow} for entity {self.name}")

        ctx = {"workflow": {"input": {}, "result": {}}}
        # parse workflow
        wf = self.workflows[workflow]
        tasks = wf.replace(" ", "").split("->")

        for i, task in enumerate(tasks):
            if tasks[i - 1] in ctx["workflow"]["result"]:
                ctx["workflow"]["input"][task] = ctx["workflow"]["result"][tasks[i - 1]]

            ctx["workflow"]["result"][task] = self.service_manager.run_task(task, ctx)

        return ctx


class EntityManager:
    def __init__(self, service_manager: ServiceManager = None):
        self.entities = {}
        self.__main_service_manager = service_manager or ServiceManager()
        logger.debug(f"Created new entity manager {self}")

    @property
    def service_manager(self) -> ServiceManager:
        if self.__main_service_manager is None:
            self.__main_service_manager = ServiceManager()
            logger.debug(f"Created new service manager {self.__main_service_manager}")
        return self.__main_service_manager

    def load_entities(self, entities: list[Path]):
        for entity in entities:
            E = Entity.load_from_yaml(entity)
            self.entities[E.name] = E

            # copy common services from main service manager
            for service in E.services:
                if service in self.service_manager.services:
                    logger.debug(f"Copying service {service} to {E.name}")
                    E.service_manager.services[service] = self.service_manager.services[
                        service
                    ]

        logger.debug(f"Loaded entities {self.entities.keys()}")

    def get_entity(self, entity: str) -> Optional[Entity]:
        if entity in self.entities:
            return self.entities[entity]
        return None

    def get_entities(self) -> list[Entity]:
        return list(self.entities.values())

    def get_entity_names(self) -> list[str]:
        return list(self.entities.keys())

    def get_entity_items(self) -> list[tuple[str, list[str]]]:
        return [(e.name, e.services) for e in self.entities.values()]

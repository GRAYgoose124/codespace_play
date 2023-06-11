import json
from dataclass_wizard import YAMLWizard

from dataclasses import dataclass, field
from .service import Service


@dataclass
class ServiceManager(YAMLWizard):
    """A class to manage services."""

    services: dict[str, Service] = field(default_factory=dict)

    def get_service(self, service_name: str) -> Service:
        try:
            return self.services[service_name]
        except KeyError:
            raise KeyError(f"Service {service_name} does not exist.")

    def get_services(self) -> list[Service]:
        return list(self.services.values())

    def add_service(self, service: Service) -> None:
        if service.name in self.services:
            raise KeyError(f"Service {service.name} already exists.")

        self.services[service.name] = service

    def remove_service(self, service_name: str) -> None:
        try:
            del self.services[service_name]
        except KeyError:
            raise KeyError(f"Service {service_name} does not exist.")

    def update_service(self, service_name: str, service: Service) -> None:
        try:
            self.remove_service(service_name)
        except KeyError:
            pass

        self.add_service(service)

    def save(self, path: str) -> None:
        self.to_yaml_file(path)

    def reload(self, path) -> None:
        self.services = ServiceManager.load(path).services

    @staticmethod
    def load(path: str) -> "ServiceManager":
        man = ServiceManager.from_yaml_file(path)

        man._load_all_services()
        return man

    def _load_all_services(self) -> None:
        for service in self.services.values():
            service.load_module()

from pathlib import Path

import yaml

data_root = Path(__file__).parent.parent.parent / "data"

# Daemon settings
daemon_settings_file = data_root / "settings.yml"

# Common services and tasks
common_service_dir = data_root / "common_services"
entities_dir = data_root / "entities"

with open(daemon_settings_file, "r") as f:
    settings = yaml.safe_load(f)["settings"]
    default_common_services = settings["common_services"]
    default_entities = settings["entities"]

    _all_common_service_files = [
        common_service_dir / s / "service.yml"
        for s in common_service_dir.iterdir()
        if s.is_dir()
    ]

    _all_entity_files = [
        entities_dir / e / "entity.yml" for e in entities_dir.iterdir() if e.is_dir()
    ]

all_common_services = {
    s.name: f for s, f in zip(common_service_dir.iterdir(), _all_common_service_files)
}
common_services = {
    s: f for s, f in all_common_services.items() if s in default_common_services
}


all_entities = {e.name: f for e, f in zip(entities_dir.iterdir(), _all_entity_files)}
default_entities = {e: f for e, f in all_entities.items() if e in default_entities}


__all__ = [
    "data_root",
    "daemon_settings_file",
    "all_common_services",
    "all_entities",
    "common_services",
    "default_entities",
]

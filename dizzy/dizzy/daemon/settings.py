""" Settings for the daemon

Anything can use these, but really this is for the daemon.server. The daemon.client should pretend
to be unaware of these settings in development. In production, the client should be
on separate hardware from the server, only communicating via JSON-RPC.

Important symbols:
    data_root: Path
        The root path for all daemon data
    common_services: dict
        A dict of all common services
    all_entities: dict
        A dict of all entities


Daemon specific settings:
    - These are configured from the `(data_root / "settings.yml")` file:
    default_common_services: dict
        A dict of all default common services
    default_entities: dict
        A dict of all default entities


Lesser important symbols:
    daemon_settings_file: Path
        The path to the daemon settings file
"""
from pathlib import Path

import yaml


# Root path for all daemon data, todo: make this configurable/discoverable.
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

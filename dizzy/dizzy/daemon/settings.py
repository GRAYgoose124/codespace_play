from pathlib import Path

import yaml

data_root = Path(__file__).parent.parent.parent / "data"

# Daemon settings
daemon_settings_file = data_root / "settings.yml"

# Common services and tasks
common_service_dir = data_root / "common_services"
entities_dir = data_root / "entities"

# default_common_services = ["uno"]
# default_entities = ["einz", "zwei", "drei"]
with open(daemon_settings_file, "r") as f:
    settings = yaml.safe_load(f)["settings"]
    default_common_services = settings["common_services"]
    default_entities = settings["entities"]


_default_service_files = [
    common_service_dir / s / "service.yml" for s in default_common_services
]
common_services = {
    s: f for s, f in zip(default_common_services, _default_service_files)
}

_all_common_service_files = [
    common_service_dir / s / "service.yml"
    for s in common_service_dir.iterdir()
    if s.is_dir()
]
all_common_services = {
    s.name: f for s, f in zip(common_service_dir.iterdir(), _all_common_service_files)
}

# Entities which can be loaded by the daemon (through an EntityLoader)
_entity_dirs = [e.name for e in entities_dir.iterdir() if e.is_dir()]

# remove entities that don't have yml files
entities = [
    e
    for e in _entity_dirs
    if any(
        [
            f.is_file()
            for f in (entities_dir / e).iterdir()
            if f.suffix in [".yml", ".yaml"]
        ]
    )
]
# _default_entity_files = [
#     entities_dir / e / "entity.yml" for e in default_entities if e in entities
# ]
# default_entities = {e: f for e, f in zip(default_entities, _default_entity_files)}

_all_entity_files = [
    entities_dir / e / "entity.yml" for e in entities_dir.iterdir() if e.is_dir()
]
all_entities = {e.name: f for e, f in zip(entities_dir.iterdir(), _all_entity_files)}

default_entities = {e: f for e, f in all_entities.items() if e in default_entities}

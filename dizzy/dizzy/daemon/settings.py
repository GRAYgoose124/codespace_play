from pathlib import Path

data_root = Path(__file__).parent.parent.parent / "data"

# Common services and tasks
common_service_dir = data_root / "common_services"
entities_dir = data_root / "entities"

default_common_services = ["uno"]
default_entities = ["einz", "zwei", "drei"]


_default_service_files = [
    common_service_dir / s / "service.yml" for s in default_common_services
]
common_services = {
    s: f for s, f in zip(default_common_services, _default_service_files)
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
_default_entity_files = [
    entities_dir / e / "entity.yml" for e in default_entities if e in entities
]
default_entities = {e: f for e, f in zip(default_entities, _default_entity_files)}

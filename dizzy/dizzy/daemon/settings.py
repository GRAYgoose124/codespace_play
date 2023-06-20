from pathlib import Path

data_root = Path(__file__).parent.parent.parent / "data"

common_service_dir = data_root / "common_services"
common_tasks_dir = data_root / "common_tasks"
_uno_file = common_service_dir / "uno/service.yml"
default_services = [_uno_file]


entity_dir = data_root / "entities"
entities = [e.name for e in entity_dir.iterdir() if e.is_dir()]

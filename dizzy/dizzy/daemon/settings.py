from pathlib import Path

data_root = Path(__file__).parent.parent.parent / "data"
common_service_dir = data_root / "common_services"
_uno_file = common_service_dir / "uno/service.yml"
default_services = [_uno_file]

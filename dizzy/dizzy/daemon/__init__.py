from .server import SimpleRequestServer as Server
from .client import SimpleCLIClient as Client

from .settings import data_root, common_service_dir, default_services

__all__ = ["Server", "Client", "default_services"]

from .server import SimpleRequestServer as Server
from .client import SimpleCLIClient as Client

from . import settings
from .settings import *

__all__ = [
    "Server",
    "Client",
    *settings.__all__,
]

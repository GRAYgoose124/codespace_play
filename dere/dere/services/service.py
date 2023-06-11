import importlib.util

from pathlib import Path
from typing import Optional
from dataclass_wizard import YAMLWizard
from dataclasses import dataclass, field


@dataclass
class Service(YAMLWizard):
    name: str
    description: str
    module_path: str
    import_path: str

    def __post_init__(self):
        self.__loaded_module: Optional[object] = None

    def load_module(self) -> object:
        if self.__loaded_module is None:
            spec = importlib.util.spec_from_file_location(
                self.import_path, self.module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.__loaded_module = module

        return self.__loaded_module

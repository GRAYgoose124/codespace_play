from pathlib import Path
from dizzy import Entity
from dizzy.daemon import all_entities


class TestEntity:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.entity = Entity.load_from_yaml(all_entities["einz"])

    def teardown_method(self):
        self.test_path.unlink()

    def test_Entity_dump(self):
        self.entity.save_to_yaml(self.test_path)
        test_E = Entity.load_from_yaml(self.test_path)

        assert self.test_path.exists()
        assert test_E.name == "einz"
        assert not hasattr(test_E, "__services_root")

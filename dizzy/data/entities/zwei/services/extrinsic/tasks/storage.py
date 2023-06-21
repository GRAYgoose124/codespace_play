import json
from dizzy import Task
from dizzy.daemon import data_root


class Store(Task):
    """storage task, see 'store.json'"""

    @staticmethod
    def run(ctx):
        with open(data_root / "store.json", "w") as f:
            f.write(json.dumps(ctx))

        return "Unused, see 'store.json'"

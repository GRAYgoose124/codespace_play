import asyncio
from random import randint
from typing import Any
from typing_extensions import override

from .json import JsonPeer


class RandomPeer(JsonPeer):
    # singleton class var for counter
    _counter = 0

    @staticmethod
    async def RANDOM_handler(peer: "RandomPeer", message):
        data = await JsonPeer.JSON_handler(peer, message)

        RandomPeer._counter += int(data["random"])
        print(f"GOT THAT RANDOM GOODNESS: {RandomPeer._counter}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("JSON", self.RANDOM_handler, overwrite=True)

    async def workload(self) -> dict[str, Any]:
        data = await super().workload()
        data.update({"random": randint(1, 100)})

        await asyncio.sleep(1.0)
        return data

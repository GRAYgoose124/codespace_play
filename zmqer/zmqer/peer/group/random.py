import asyncio
from random import randint
from typing_extensions import override

from .json import JsonPeer


class RandomPeer(JsonPeer):
    # singleton class var for counter
    _counter = 0

    @staticmethod
    async def RANDOM_handler(peer: "RandomPeer", message):
        data = super().JSON_handler(peer, message)

        RandomPeer._counter += int(data["random"])
        print(f"GOT THAT RANDOM GOODNESS: {RandomPeer._counter}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("JSON", self.RANDOM_handler, overwrite=True)

    async def workload(self):
        data = await super().workload()
        data.update({"random": randint(1, 100)})

        await asyncio.sleep(3.0)
        return data

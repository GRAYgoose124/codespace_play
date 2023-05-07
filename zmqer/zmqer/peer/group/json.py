import asyncio
import json
import time
from random import randint
from typing import Any

from . import WorkloadPeer


class JsonPeer(WorkloadPeer):
    @staticmethod
    async def JSON_handler(peer: "JsonPeer", workload: str):
        """Parse json message"""
        # do something with the message as dict
        try:
            data = json.loads(workload)

            return data
        except json.JSONDecodeError as e:
            peer.logger.error(f"Error: {e}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("JSON", self.JSON_handler)

    def workload(self) -> dict[str, Any]:
        output = {"JSON": f"{time.time()}"}
        return output

    async def workload_wrapper(self) -> str:
        await asyncio.sleep(1.0)
        return json.dumps(getattr(self, "workload")())


class RandomPeer(JsonPeer):
    # singleton class var for counter
    _counter = 0

    @staticmethod
    async def RANDOM_handler(peer: "RandomPeer", workload):
        data = await JsonPeer.JSON_handler(peer, workload)

        RandomPeer._counter += int(data["random"])
        print(f"GOT THAT RANDOM GOODNESS: {RandomPeer._counter}")

    def __post_init__(self):
        # super().__post_init__()
        self.register_message_type("JSON", self.RANDOM_handler)  # , overwrite=True)

    def workload(self) -> dict[str, Any]:
        data = super().workload()
        data.update({"random": randint(1, 100)})

        return data

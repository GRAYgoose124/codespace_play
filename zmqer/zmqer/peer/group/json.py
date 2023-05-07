from abc import ABCMeta, abstractmethod
import asyncio
import json
import time
from random import randint
from typing import Any

from . import WorkloadPeer


# S/N: We don't need to explicitly state ABCMeta because the base Peer is an ABC.
class JsonPeer(WorkloadPeer, metaclass=ABCMeta):
    @staticmethod
    async def JSON_handler(peer: "JsonPeer", workload: str):
        """Parse json message"""
        try:
            data = json.loads(workload)

            return peer.handle_work(data)

        except json.JSONDecodeError as e:
            peer.logger.error(f"Error: {e}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("JSON", self.JSON_handler)

    @abstractmethod
    def workload(self) -> dict[str, Any]:
        output = {"JSON": f"{time.time()}"}
        return output

    async def workload_wrapper(self) -> str:
        await asyncio.sleep(1.0)
        return json.dumps(getattr(self, "workload")())


class RandomPeer(JsonPeer):
    # singleton class var for counter
    _counter = 0

    def handle_work(self, data: dict[str, Any]):
        """Handle the workload"""
        RandomPeer._counter += int(data["random"])
        print(f"GOT THAT RANDOM GOODNESS: {RandomPeer._counter}")

    def workload(self) -> dict[str, Any]:
        """Produces a random workload"""
        data = super().workload()
        data.update({"random": randint(1, 100)})

        return data


class RandomNetSeparatedPeer(JsonPeer):
    def __init__(self, *args, **kwargs):
        self._counter = 0
        super().__init__(*args, **kwargs)

    def handle_work(self, data: dict[str, Any]):
        """Handle the workload"""
        self._counter += int(data["random"])
        print(f"GOT THAT RANDOM GOODNESS: {RandomPeer._counter}")

    def workload(self) -> dict[str, Any]:
        """Produces a random workload"""
        data = super().workload()
        data.update({"random": randint(1, 100)})

        return data

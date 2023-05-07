import asyncio
import json
from random import randint

from .group import GroupPeer


class JsonPeer(GroupPeer):
    @staticmethod
    def JSON_handler(peer: "JsonPeer", message: str) -> str:
        """Parse json message"""
        # do something with the message as dict
        try:
            data = json.loads(message)

            # print(f"Got JSON: {data}")
        except json.JSONDecodeError as e:
            peer.logger.error(f"Error: {e}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("JSON", self.JSON_handler)

    async def broadcast_loop(self):
        while not self._done:
            try:
                await asyncio.sleep(3.0)
                data = {"random": randint(1, 100)}
                await self.broadcast("JSON", json.dumps(data))
            except Exception as e:
                self.logger.error(f"Error: {e}")

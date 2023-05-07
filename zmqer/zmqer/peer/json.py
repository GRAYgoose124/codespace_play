import asyncio
import json
from random import randint

from .group import GroupPeer


class JsonPeer(GroupPeer):
    @staticmethod
    def JSON_handler(peer: "JsonPeer", message: str) -> dict:
        """Parse json message and return dict."""
        return json.loads(message)

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("JSON", self.RANDOM_handler)

    async def broadcast_loop(self):
        while not self._done:
            try:
                await asyncio.sleep(3.0)
                data = {"random": randint(1, 100)}
                await self.broadcast("JSON", json.dumps(data))
            except Exception as e:
                self.logger.error(f"Error: {e}")

import asyncio
from random import randint

from .json import JsonPeer as Peer


class RandomPeer(Peer):
    # singleton class var for counter
    _counter = 0

    @staticmethod
    async def RANDOM_handler(peer: "RandomPeer", message):
        RandomPeer._counter += int(message)
        print(f"GOT THAT RANDOM GOODNESS: {RandomPeer._counter}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("RANDOM", self.RANDOM_handler)

    async def broadcast_loop(self):
        while not self._done:
            try:
                await asyncio.sleep(randint(1, 3))
                await self.broadcast("RANDOM", randint(1, 100))
            except Exception as e:
                self.logger.error(f"Error: {e}")

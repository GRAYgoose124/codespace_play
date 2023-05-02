from random import randint
import asyncio

from .base import Peer


class GroupPeer(Peer):
    @staticmethod
    async def JOINED_handler(peer, message):
        peer.join_statuses.append(message)
        if len(peer.join_statuses) > 100:
            peer.join_statuses.pop(0)
        peer.calculate_health()  

    @staticmethod
    async def GROUP_handler(peer, message):
        group = message.translate({ord(c): None for c in "[]' "}).split(",")
        for p in group:
            joined = peer.join_group(p)
            await peer.broadcast(f"JOINED={joined}")


class RandomGroupPeer(GroupPeer):
    def __post_init__(self):
        self.register_message_type("JOINED", self.JOINED_handler)
        self.register_message_type("GROUP", self.GROUP_handler)

    async def broadcast_loop(self):
        while not self.done:
            try:
                await asyncio.sleep(randint(1, 3))
                await self.broadcast(f"RANDOM={randint(1, 100)}")
            except Exception as e:
                self.logger.error(f"Error: {e}")

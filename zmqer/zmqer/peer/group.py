from random import randint
import asyncio

from .base import Peer
from ..misc import call_super


STATUS_LENGTH = 100


class GroupPeer(Peer):
    def __init__(self, address, group_broadcast_delay=1.0):
        # Group setup
        self.group = {}
        self.health = 0.0
        self.join_statuses = STATUS_LENGTH * [True]
        self.BASE_GROUP_BROADCAST_DELAY = group_broadcast_delay
        self.GROUP_BROADCAST_DELAY = self.BASE_GROUP_BROADCAST_DELAY

        super().__init__(address, group_broadcast_delay)

    @staticmethod
    async def JOINED_handler(peer: "GroupPeer", message):
        peer.join_statuses.append(message)
        if len(peer.join_statuses) > STATUS_LENGTH:
            peer.join_statuses.pop(0)

        health = peer.join_statuses.count("False") / STATUS_LENGTH
        peer.logger.debug(
            f"{peer.address}:\n\tPopulation health: {health} {peer.GROUP_BROADCAST_DELAY=}"
        )
        peer.health = health
        return health

    @staticmethod
    async def GROUP_handler(peer: "GroupPeer", message):
        group = message.translate({ord(c): None for c in "[]' "}).split(",")
        for p in group:
            joined = peer.join_group(p)
            await peer.broadcast(f"JOINED={joined}")

    def __post_init__(self):
        self.register_message_type("JOINED", self.JOINED_handler)
        self.register_message_type("GROUP", self.GROUP_handler)

    async def group_broadcast_loop(self):
        while not self.done:
            try:
                await asyncio.sleep(self.GROUP_BROADCAST_DELAY)

                peers = self.peers
                await self.broadcast(f"GROUP={peers}")
                self.logger.debug(f"{self.address}:\n\tBroadcasted group: {peers}")

                # Update broadcast delay based on health of the population
                if self.health < 0.5:
                    self.GROUP_BROADCAST_DELAY = max(
                        self.GROUP_BROADCAST_DELAY / (2 + (1 - self.health)), 0.25
                    )
                elif self.health > 0.9:
                    self.GROUP_BROADCAST_DELAY = self.GROUP_BROADCAST_DELAY * 2
                else:
                    self.GROUP_BROADCAST_DELAY = self.BASE_GROUP_BROADCAST_DELAY
            except Exception as e:
                self.logger.error(f"Error: {e}")

    def join_group(self, group_address):
        if group_address != self.address and group_address not in self.group:
            self.sub_socket.connect(group_address)
            self.group[group_address] = self.sub_socket
            self.logger.debug(
                f"{self.address}:\n\tJoined group: {group_address}\n\t\t{self.group}"
            )
            return True
        return False

    def setup(self):
        super().setup()
        self._tasks.append(self.loop.create_task(self.group_broadcast_loop()))

        return self.tasks


class RandomGroupPeer(GroupPeer):
    # singleton class var for counter
    _counter = 0

    @staticmethod
    async def RANDOM_handler(peer: "RandomGroupPeer", message):
        RandomGroupPeer._counter += int(message)
        print(f"GOT THAT RANDOM GOODNESS: {RandomGroupPeer._counter}")

    def __post_init__(self):
        super().__post_init__()
        self.register_message_type("RANDOM", self.RANDOM_handler)

    async def broadcast_loop(self):
        while not self.done:
            try:
                await asyncio.sleep(randint(1, 3))
                await self.broadcast(f"RANDOM={randint(1, 100)}")
            except Exception as e:
                self.logger.error(f"Error: {e}")

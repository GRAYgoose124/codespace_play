from random import randint
import asyncio

from .base import Peer
from ..misc import call_super


STATUS_LENGTH = 100
NEW_PEER_DAMAGE = STATUS_LENGTH // 10


class GroupPeer(Peer):
    def __init__(self, address, group_broadcast_delay=1.0):
        # Group setup
        self.group = {}
        self.health = 0.0
        self.join_statuses = STATUS_LENGTH * [True]
        self.broadcast_statuses = STATUS_LENGTH * [True]
        self.GROUP_BROADCAST_DELAY = group_broadcast_delay
        self.PERCENT_GROUP_IS_ANNOUNCER = 0.1
        self.IS_GROUP_ANNOUNCER = True

        super().__init__(address, group_broadcast_delay)

    @staticmethod
    async def JOINED_handler(peer: "GroupPeer", message):
        """Procced by a peer joining a group.

        The peer's health is updated based on the join status.

        If no JOINED=True messages are received, the peer's health is maximized
        as this means that all peers are in the group.
        """
        # Lets make a new peer hurt the population.
        if message == "True":
            message = [True] * NEW_PEER_DAMAGE
        if message == "False":
            message = [False]

        peer.join_statuses = message + peer.join_statuses
        if len(peer.join_statuses) > STATUS_LENGTH:
            peer.join_statuses = peer.join_statuses[:STATUS_LENGTH]

        # Health is maximized when all joins were false.
        health = peer.join_statuses.count(False) / STATUS_LENGTH
        peer.logger.debug(
            f"{peer.address}:\n\tPopulation health: {health} {peer.GROUP_BROADCAST_DELAY=}"
        )
        peer.health = health
        return health

    @staticmethod
    async def GROUP_handler(peer: "GroupPeer", message):
        """Procced by an enabled group broadcast peer sending GROUP=.

        For a single broadcast peer, all peers which can receive the message
        on that peer's public group socket are in the group. Not all peers
        which receive this message will have joined the group. (connected to the sub socket)

        This will join and broadcast it's join status to the group.
        Theses statuses are used to determine the health of the population.
        """
        peer.broadcast_statuses = [True] + peer.broadcast_statuses
        if len(peer.broadcast_statuses) > STATUS_LENGTH:
            peer.broadcast_statuses = peer.join_statuses[:STATUS_LENGTH]

        # Parse peer list from message
        group = message.translate({ord(c): None for c in "[]' "}).split(",")

        # join the group of each peer - union of all peer's groups.
        for p in group:
            joined = peer.join_group(p)
            # We broadcast our join status to the group for health monitoring.
            await peer.broadcast(f"JOINED={joined}")

        return group

    @staticmethod
    async def ANNOUNCER_handler(peer: "GroupPeer", message):
        """Procced by an enabled group broadcast peer sending ANNOUNCER=.

        Used to determine democratic vote on the next announcers when a new
        group broadcast stage

        If there are not enough announcers, a peer receiving this message will
        become an announcer.

        If the health is at 1.0, only one announcer is needed and receiving this
        message will disable the peer's announcer status.

        If the health is at 0.0, all peers will become announcers and receiving
        this message will enable the peer's announcer status.

        if 0.0 < health < 1.0, the number of announcers is proportional to the
        health of the population. At 0.5, percentage*half of the population will be
        announcers.


        """

    def __post_init__(self):
        self.register_message_type("JOINED", self.JOINED_handler)
        self.register_message_type("GROUP", self.GROUP_handler)
        self.register_message_type("ANNOUNCER", self.ANNOUNCER_handler)

    async def group_broadcast_stage(self):
        while not self._done:
            try:
                broadcast_ratio = self.broadcast_statuses.count(True) / STATUS_LENGTH
                if self.health < broadcast_ratio:
                    peers = self.peers
                    await self.broadcast(f"GROUP={peers}")
                    self.logger.debug(
                        f"{self.address}:\n\tBroadcasted group: {peers}\n\t\t{broadcast_ratio=}"
                    )
                    self.broadcast_statuses = [False] + self.broadcast_statuses
                    if len(self.broadcast_statuses) > STATUS_LENGTH:
                        self.broadcast_statuses = self.broadcast_statuses[
                            :STATUS_LENGTH
                        ]

                # Update broadcast delay based on health of the population
                # DEMOCRATIC GROUP LOGIC
                # If a population is healthy, decrease the number of nodes performing group announcements.
                # 1.0 == 100% of the population is healthy, every node has every other node in its group.
                # 0.0 == 0% of the population is healthy, no node has enough(coupled to STATUS_LENGTH) nodes in its group.
                # At 1.0, we only need one node to broadcast the group.
                # At 0.0, we want every node or some percentage to broadcast the group.
                # The broadcast delay is now fixed per node, so that we only need to adjust the number of nodes broadcasting.
                await asyncio.sleep(self.GROUP_BROADCAST_DELAY)
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
        self._tasks.append(self.loop.create_task(self.group_broadcast_stage()))

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
        while not self._done:
            try:
                await asyncio.sleep(randint(1, 3))
                await self.broadcast(f"RANDOM={randint(1, 100)}")
            except Exception as e:
                self.logger.error(f"Error: {e}")

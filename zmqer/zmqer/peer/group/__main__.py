import asyncio

from ...peer import Peer


STATUS_LENGTH = 100
NEW_PEER_DAMAGE = STATUS_LENGTH // 10


class GroupPeer(Peer):
    def __init__(self, *args, group_broadcast_delay=5.0, **kwargs):
        # Group setup
        self.group = {}
        self.health = 0.0
        self.join_statuses = STATUS_LENGTH * [True]
        self.broadcast_statuses = STATUS_LENGTH * [True]
        self.GROUP_BROADCAST_DELAY = group_broadcast_delay

        super().__init__(*args, **kwargs)

    @staticmethod
    async def JOINED_handler(peer: "GroupPeer", message):
        """Procced by a peer joining a group.

        The peer's health is updated based on the join status.

        If no JOINED=True messages are received, the peer's health is maximized
        as this means that all peers are in the group.
        """
        # Lets make a new peer hurt the population.
        if message == "True":
            peer.logger.debug(f"{peer.address}:\n\tNew peer joined")
            message = [True] * NEW_PEER_DAMAGE
        if message == "False":
            message = [False]

        peer.join_statuses = message + peer.join_statuses
        if len(peer.join_statuses) > STATUS_LENGTH:
            peer.join_statuses = peer.join_statuses[:STATUS_LENGTH]

        # Health is maximized when all joins were false.
        peer.health = peer.join_statuses.count(False) / STATUS_LENGTH
        peer.logger.debug(
            f"{peer.address}:\n\tPopulation health: {peer.health}\t broadcast ratio: {peer.broadcast_ratio}"
        )
        return peer.health

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
        joined = False
        for p in group:
            joined = joined or peer.join_group(p)
            # We broadcast our join status to the group for health monitoring.

        # Technically this means if we join any group, we're going to
        # damage all groups. this is fine.
        await peer.broadcast("JOINED", joined)

        return group

    def __post_init__(self):
        self.register_message_type("JOINED", self.JOINED_handler)
        self.register_message_type("GROUP", self.GROUP_handler)

    async def group_broadcast_stage(self):
        while not self._done:
            try:
                self.broadcast_ratio = (
                    self.broadcast_statuses.count(True) / STATUS_LENGTH
                )
                if self.health < self.broadcast_ratio:
                    peers = self.peers
                    await self.broadcast("GROUP", peers)
                    self.logger.debug(
                        f"{self.address}:\n\tBroadcasted group: {peers}\n\t\t{self.broadcast_ratio=}"
                    )
                    self.broadcast_statuses = [False] + self.broadcast_statuses
                    if len(self.broadcast_statuses) > STATUS_LENGTH:
                        self.broadcast_statuses = self.broadcast_statuses[
                            :STATUS_LENGTH
                        ]

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

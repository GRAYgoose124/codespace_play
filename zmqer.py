import asyncio
from itertools import combinations
import os
from random import randint
import time
import logging
import zmq.asyncio


class Peer:
    def __init__(self, address, group_broadcast_rate=5.0):
        self.address = address
        self.GROUP_BROADCAST_RATE = group_broadcast_rate

        self.loop = asyncio.get_event_loop()
        self.ctx = zmq.asyncio.Context()

        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(self.address)

        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.group = {}

        self.logger = logging.getLogger(self.__class__.__name__)
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler(f"logs/{self.address[6:]}debug.log")
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    async def recv(self):
        message = await self.sub_socket.recv_string()
        self.logger.debug(f"{self.address}:\n\tReceived message: {message}")
        return message

    def handle_NEW_PEER(self, message):
        self.join_group(message)
        # TODO: broadcast JOINED_GROUP=group_address so that the population health can be determined.
        self.logger.debug(
            f"{self.address}:\n\tReceived NEW_PEER message: {message}\n{self.group}"
        )

    async def recv_loop(self):
        self.sub_socket.connect(self.address)
        while True:
            try:
                message = await self.recv()
                if message.startswith("NEW_PEER"):
                    self.handle_NEW_PEER(message[9:])
            except Exception as e:
                self.logger.error(f"Error: {e}")

    async def broadcast(self, message):
        await self.pub_socket.send_string(message)
        self.logger.debug(f"{self.address}:\n\tSent message: {message}")

    async def broadcast_loop(self):
        while True:
            try:
                await asyncio.sleep(1)
                await self.broadcast(f"{self.address} gave {randint(0, 100)}")
                if time.time() % self.GROUP_BROADCAST_RATE < 1.0:
                    await self.broadcast_group()
            except Exception as e:
                self.logger.error(f"Error: {e}")

    def join_group(self, group_address):
        if group_address != self.address and group_address not in self.group:
            self.sub_socket.connect(group_address)
            self.group[group_address] = self.sub_socket
            self.logger.debug(
                f"{self.address}:\n\tJoined group: {group_address}\n\t\t{self.group}"
            )

    def get_group_peers(self) -> list["Peer"]:
        return list(self.group.keys())

    async def broadcast_group(self):
        """send the peers connected in the group"""
        peers = self.get_group_peers()
        for peer in peers:
            await self.broadcast(f"NEW_PEER={peer}")

        self.logger.debug(f"{self.address}:\n\tBroadcasted group: {peers}")


def connect_all(peers):
    for p, p2 in combinations(peers, 2):
        p.join_group(p2.address)
        p2.join_group(p.address)


def connect_linked(peers):
    for p, p2 in zip(peers, peers[1:]):
        p.join_group(p2.address)

    peers[-1].join_group(peers[0].address)


def main():
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()

    starting_port = 5555 + randint(0, 1000)
    n_peers = 3

    peers = [
        Peer(address)
        for address in [
            f"tcp://127.0.0.1:{port}"
            for port in range(starting_port, starting_port + n_peers)
        ]
    ]

    connect_linked(peers)

    for peer in peers:
        loop.create_task(peer.recv_loop())
        loop.create_task(peer.broadcast_loop())

    loop.run_forever()


if __name__ == "__main__":
    main()

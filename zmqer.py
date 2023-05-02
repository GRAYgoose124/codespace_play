import asyncio
from itertools import combinations
import os
from random import randint, random
import time
import logging
import zmq.asyncio


class Peer:
    def __init__(self, address, group_broadcast_delay=1.0):
        # Peer setup
        self.address = address
        self.done = False

        # ZMQ / asyncio setup
        self.loop = asyncio.get_event_loop()
        self.ctx = zmq.asyncio.Context()
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # Group setup
        self.group = {}
        self.health = 0.0
        self.join_statuses = 100 * [True]
        self.BASE_GROUP_BROADCAST_DELAY = group_broadcast_delay
        self.GROUP_BROADCAST_DELAY = self.BASE_GROUP_BROADCAST_DELAY

        # Logging setup
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.propagate = False
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler(f"logs/{self.address[6:]}.log")
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    async def broadcast(self, message):
        await self.pub_socket.send_string(message)
        self.logger.debug(f"{self.address}:\n\tSent message: {message}")

    def join_group(self, group_address):
        if group_address != self.address and group_address not in self.group:
            self.sub_socket.connect(group_address)
            self.group[group_address] = self.sub_socket
            self.logger.debug(
                f"{self.address}:\n\tJoined group: {group_address}\n\t\t{self.group}"
            )
            return True
        return False

    @property
    def peers(self) -> list["Peer"]:
        return [self.address] + list(self.group.keys())
    
    def calculate_health(self):
        health = self.join_statuses.count("False") / 100
        self.logger.debug(
            f"{self.address}:\n\tPopulation health: {health} {self.GROUP_BROADCAST_DELAY=}"
        )
        self.health = health
        return health
    
    async def recv_loop(self):
        while not self.done:
            try:
                message = await self.sub_socket.recv_string()
                self.logger.debug(f"{self.address}:\n\tReceived message: {message}")

                if message.startswith("JOINED="):
                    self.join_statuses.append(message[7:])
                    if len(self.join_statuses) > 100:
                        self.join_statuses.pop(0)
                    self.calculate_health()

                elif message.startswith("GROUP="):
                    group = message[6:].translate({ord(c): None for c in "[]' "}).split(",")
                    for peer in group:
                        joined = self.join_group(peer)
                        await self.broadcast(f"JOINED={joined}")
            except Exception as e:
                self.logger.error(f"Error: {e}")
            
    async def broadcast_loop(self):
        while not self.done:
            try:
                # TODO: this sleep is to simulate some work being done
                await asyncio.sleep(1)
                await self.broadcast(f"{self.address} gave {randint(0, 100)}")
            except Exception as e:
                self.logger.error(f"Error: {e}")

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

    def setup(self):
        self.done = False
        self.pub_socket.bind(self.address)
        self.sub_socket.connect(self.address)

        self._tasks = [
            self.loop.create_task(self.recv_loop()),
            self.loop.create_task(self.group_broadcast_loop()),
            self.loop.create_task(self.broadcast_loop())
        ]

        return self._tasks
    
    def teardown(self):
        self.done = True
        for task in self._tasks:
            task.cancel()

        self.sub_socket.close()
        self.pub_socket.close()


def connect_all(peers):
    for p, p2 in combinations(peers, 2):
        p.join_group(p2.address)
        p2.join_group(p.address)


def connect_linked(peers):
    for p, p2 in zip(peers, peers[1:]):
        p.join_group(p2.address)

    peers[-1].join_group(peers[0].address)


def connect_random(peers):
    for p, p2 in combinations(peers, 2):
        if random() < 0.5:
            p.join_group(p2.address)
            p2.join_group(p.address)


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.root.handlers[0].stream = None
    loop = asyncio.get_event_loop()

    starting_port = 5555 + randint(0, 1000)
    n_peers = 5

    peers = [
        Peer(address)
        for address in [
            f"tcp://127.0.0.1:{port}"
            for port in range(starting_port, starting_port + n_peers)
        ]
    ]

    connect_linked(peers)

    tasks = []
    for peer in peers:
        tasks.extend(peer.setup())

    loop.run_until_complete(asyncio.gather(*tasks))



if __name__ == "__main__":
    main()

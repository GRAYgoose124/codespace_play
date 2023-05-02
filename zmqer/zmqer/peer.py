import zmq.asyncio
import os
import asyncio
import logging
from random import randint


class Peer:
    def __init__(self, address, group_broadcast_delay=1.0, setup=False):
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

        if setup:
            self.setup()

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

    def __repr__(self):
        return f"<Peer {self.address}>"
    
    def __str__(self):
        return self.address
    
    def __hash__(self):
        return hash(self.address)
    
    def __eq__(self, other):
        return self.address == other.address
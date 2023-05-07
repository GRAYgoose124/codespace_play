from abc import ABC, abstractmethod
import zmq.asyncio
import os
import asyncio
import logging


class Peer(ABC):
    def __init__(self, address, group_broadcast_delay=1.0):
        # Peer setup
        self.address = address
        self._done = False
        self._tasks = []

        # ZMQ / asyncio setup
        self.loop = asyncio.get_event_loop()
        self.ctx = zmq.asyncio.Context()
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.message_types = {}

        # Logging setup
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.propagate = False

        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler(f"logs/{self.address[6:]}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(logging.Filter(self.__class__.__name__))
        self.logger.addHandler(file_handler)

        self.__post_init__()

    def __post_init__(self):
        pass

    @abstractmethod
    async def broadcast_loop(self):
        pass

    async def broadcast(self, message):
        await self.pub_socket.send_string(message)
        self.logger.debug(f"{self.address}:\n\tSent message: {message}")

    @property
    def tasks(self):
        return self._tasks

    @property
    def done(self):
        return self._done

    @property
    def peers(self) -> list["Peer"]:
        return [self.address] + list(self.group.keys())

    def register_message_type(self, message_type, handler):
        if message_type not in self.message_types:
            self.message_types[message_type] = handler

    async def message_type_handler(self, message):
        for message_type, handler in self.message_types.items():
            if message.startswith(f"{message_type}="):
                return await handler(self, message[len(message_type) + 1 :])

    async def recv_loop(self):
        while not self.done:
            try:
                message = await self.sub_socket.recv_string()
                self.logger.debug(f"{self.address}:\n\tReceived message: {message}")

                await self.message_type_handler(message)
            except Exception as e:
                self.logger.error(f"Error: {e}")

    def setup(self):
        self._done = False
        self.pub_socket.bind(self.address)
        self.sub_socket.connect(self.address)

        self._tasks = [
            self.loop.create_task(self.recv_loop()),
            self.loop.create_task(self.broadcast_loop()),
        ]

        return self._tasks

    async def teardown(self):
        self._done = True
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks = []

        self.sub_socket.close()
        self.pub_socket.close()

    def __repr__(self):
        return f"<Peer {str(self)}>"

    def __str__(self):
        return self.address

    def __hash__(self):
        return hash(self.address)

    def __eq__(self, other):
        return self.address == other.address

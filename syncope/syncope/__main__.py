import asyncio
import zmq.asyncio


class Peer:
    def __init__(self, payload, is_server):
        self.payload = payload
        self.is_server = is_server

    async def run(self):
        context = zmq.asyncio.Context()
        if self.is_server:
            socket = context.socket(zmq.REP)
            socket.bind("tcp://127.0.0.1:5555")
        else:
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://127.0.0.1:5555")

        if self.is_server:
            while True:
                message = await socket.recv()
                print(f"Received message: {message}")
                response = f"Echoing '{message.decode()}' with payload {self.payload}"
                await socket.send_string(response)
        else:
            for request in self.payload:
                await socket.send(request)
                response = await socket.recv()
                print(f"Received response: {response}")


async def main():
    peer1 = Peer(b"Hello", True)
    peer2 = Peer([b"World", b"!"], False)
    tasks = [asyncio.create_task(peer1.run()), asyncio.create_task(peer2.run())]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

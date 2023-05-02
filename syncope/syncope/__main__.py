import asyncio
import zmq.asyncio


async def server():
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://127.0.0.1:5555")
    while True:
        message = await socket.recv()
        print(f"Received message: {message}")
        response = f"Echoing '{message.decode()}'"
        await socket.send_string(response)


async def client():
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:5555")
    for request in [b"Hello", b"World", b"!"]:
        await socket.send(request)
        response = await socket.recv()
        print(f"Received response: {response}")


async def asy_main():
    tasks = [asyncio.create_task(server()), asyncio.create_task(client())]
    await asyncio.gather(*tasks)


def main():
    asyncio.run(asy_main())


if __name__ == "__main__":
    main()

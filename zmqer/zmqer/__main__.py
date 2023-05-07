import asyncio
from random import randint

import logging

from zmqer.peer.group import RandomGroupPeer as Peer
from zmqer.misc import connect_linked


def main():
    logging.basicConfig(level=logging.DEBUG)
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

    coroutines = set()
    # Create a set of tasks
    for i, peer in enumerate(peers):
        if i == n_peers - 1:

            async def delay_wrapper():
                await asyncio.sleep(10)
                logging.info("Delaying peer setup")
                ts = peer.setup()
                coroutines.update(ts)

            coroutines.add(delay_wrapper())
        else:
            coroutines.update(peer.setup())

    try:
        fut = asyncio.gather(*coroutines)
        loop.run_until_complete(fut)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, cancelling tasks...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()

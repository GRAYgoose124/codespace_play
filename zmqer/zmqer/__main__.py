import asyncio
from random import randint

import logging

from zmqer.peer import Peer
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

    tasks = []
    for peer in peers:
        tasks.extend(peer.setup())

    loop.run_until_complete(asyncio.gather(*tasks))



if __name__ == "__main__":
    main()

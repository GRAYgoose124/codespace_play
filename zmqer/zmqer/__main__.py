import asyncio
from random import randint
import logging
import shutil
import os

from zmqer.misc import connect_linked

from zmqer.peer import JsonPeer as Peer


async def teardown_peers(peers):
    # Use gather to teardown all peers concurrently
    await asyncio.gather(*(p.teardown() for p in peers), return_exceptions=True)


def main():
    PEER_SETUP_DELAY = 30.0

    # setup logging
    log_to = "stdout"
    log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    #   reset logs - if using file handlers
    if log_to == "file":
        if os.path.exists("logs"):
            shutil.rmtree("logs")
        os.makedirs("logs")

    # Instantiate peers for a random port range from starting_port to starting_port+n_peers.
    starting_port = 5555 + randint(0, 1000)
    n_peers = 20

    #   Log first peer to stdout
    peers = [
        Peer(f"tcp://127.0.0.1:{starting_port}", log_to="stdout", log_level=log_level)
    ]
    #    Initialize the rest of the peers
    peers += [
        Peer(address)
        for address in [
            f"tcp://127.0.0.1:{port}"
            for port in range(starting_port + len(peers), starting_port + n_peers)
        ]
    ]

    connect_linked(peers)

    coroutines = set()
    # Create a set of tasks
    for i, peer in enumerate(peers):
        if i >= n_peers // 2:
            peer.logger.debug("Delaying peer setup")

            async def delay_wrapper(task):
                await asyncio.sleep(PEER_SETUP_DELAY)
                peer.logger.debug(
                    f"Running delayed peer.setup() task: {task.__class__.__name__}..."
                )
                await task

            for task in peer.setup():
                coroutines.add(delay_wrapper(task))
        else:
            coroutines.update(peer.setup())

    try:
        # event loop
        loop = asyncio.get_event_loop()

        fut = asyncio.gather(*coroutines)
        loop.run_until_complete(fut)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, cancelling tasks...")
        fut.cancel()
        loop.run_until_complete(
            asyncio.gather(*(teardown_peers(peers), fut), return_exceptions=True)
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()

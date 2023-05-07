import asyncio
from random import randint
import logging
import shutil
import os
import argparse

from zmqer.misc import connect_linked

from zmqer.peer import RandomPeer as Peer


async def teardown_peers(peers):
    # Use gather to teardown all peers concurrently
    await asyncio.gather(*(p.teardown() for p in peers), return_exceptions=True)


def argparser():
    parser = argparse.ArgumentParser()
    # logging
    parser.add_argument(
        "-lt",
        "--log-to",
        type=str,
        default="stdout",
        choices=["stdout", "file", None],
        help="Where to log output.",
    )
    parser.add_argument(
        "-v",
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "v"],
        help="Logging level",
    )
    parser.add_argument(
        "-la",
        "--log-all",
        action="store_true",
        help="Log all messages, not just those from specified logging peers.",
    )

    # peer setup
    parser.add_argument(
        "-psd",
        "--peer-setup-delay",
        type=float,
        default=30.0,
        help="Delay in seconds before setting up late-start peers.",
    )
    parser.add_argument(
        "-n",
        "--n-peers",
        type=int,
        default=20,
        help="Number of peers to instantiate.",
    )
    parser.add_argument(
        "-nl",
        "--n-late-start-peers",
        type=float,
        default=0.1,
        help="Number of late-start peers to instantiate as a percentage of n_peers.",
    )
    parser.add_argument(
        "-sp",
        "--starting-port",
        type=int,
        default=5555 + randint(0, 1000),
        help="Starting port for peer addresses. (defaults to 5555+randint(1000))",
    )

    args = parser.parse_args()
    if args.log_level == "v":
        args.log_level = "DEBUG"

    return args


def main():
    args = argparser()
    # setup logging
    logging.basicConfig(level=args.log_level)

    #   reset logs - if using file handlers
    if args.log_to == "file":
        if os.path.exists("logs"):
            shutil.rmtree("logs")
        os.makedirs("logs")

    # Instantiate peers for a random port range from starting_port to starting_port+n_peers.

    #   Log first peer to stdout
    peers = [
        Peer(
            f"tcp://127.0.0.1:{args.starting_port}",
            log_to=args.log_to,
            log_level=args.log_level,
        )
    ]
    #    Initialize the rest of the peers
    peers += [
        Peer(
            address,
            log_to=args.log_to if args.log_all else None,
            log_level=args.log_level,
        )
        for address in [
            f"tcp://127.0.0.1:{port}"
            for port in range(
                args.starting_port + len(peers), args.starting_port + args.n_peers
            )
        ]
    ]

    connect_linked(peers)

    coroutines = set()
    # Create a set of tasks
    for i, peer in enumerate(peers):
        if i <= int(args.n_peers * args.n_late_start_peers):
            peer.logger.debug("Delaying peer setup")

            async def delay_wrapper(task):
                await asyncio.sleep(args.peer_setup_delay)
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

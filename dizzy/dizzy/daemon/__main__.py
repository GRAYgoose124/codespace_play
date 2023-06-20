import json
import logging
from pathlib import Path
import sys
import argparse

from dizzy.daemon import Server, Client
from dizzy.daemon.settings import default_services


def server():
    server = Server()
    server.service_manager.load_services(default_services)

    print(server.service_manager.services)
    try:
        server.run()
    except KeyboardInterrupt:
        print("Server stopped.")


def client():
    client = Client()

    try:
        client.run()
    except KeyboardInterrupt:
        print("Client stopped.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["server", "client"], help="Specify either 'server' or 'client'"
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Specify the logging level",
    )
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.verbosity))

    if args.mode == "server":
        server()
    elif args.mode == "client":
        client()


if __name__ == "__main__":
    main()

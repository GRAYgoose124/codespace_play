import json
from pathlib import Path
import sys

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
    """python -m dizzy.daemon [server|client]"""
    args = sys.argv[1:]
    if len(args) == 0:
        print("Please specify either 'server' or 'client'")
        sys.exit(1)

    if args[0] == "server":
        server()
    elif args[0] == "client":
        client()


if __name__ == "__main__":
    main()

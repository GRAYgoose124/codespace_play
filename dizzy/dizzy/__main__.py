import datetime
import logging
import os
from pathlib import Path
import random
import select
import subprocess
import sys
import threading
import time


def run_server(port):
    return subprocess.Popen(
        ["dizae", "server", "-vDEBUG", f"-p{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    """A simple wrapper to start `daemon.server` and `daemon.client` with logging.

    Please see dizzy/dizzy/daemon/__main__.py for more info.
    """
    port = 5555

    print("Starting server...")
    while True:
        process = run_server(port)
        time.sleep(1)
        if process.poll() is not None and process.returncode != 0:
            print("Another server may be running...")
            # randomize port
            port = 5555 + random.randint(1, 1000)
            print(f"Trying port {port}...")
            process = run_server(port)
        else:
            print(f"Server started on port {port}.")
            break

    print(f"Starting client on port {port}...")
    try:
        subprocess.run(
            ["dizae", "client", "-vDEBUG", f"-p{port}"],
        )
    except KeyboardInterrupt:
        pass
    finally:
        process.terminate()


if __name__ == "__main__":
    main()

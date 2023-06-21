import datetime
import logging
from pathlib import Path
import select
import subprocess
import sys
import threading

from .settings import PRUNE_MINUTES


def prune(file: str, minutes: int) -> None:
    """Prune a log file to only contain the last `minutes` of logs."""
    with open(file, "r") as f:
        lines = f.readlines()

    with open(file, "w") as f:
        for i, line in enumerate(lines):
            if line.startswith("--- ") and line.endswith(" ---\n"):
                date = datetime.datetime.strptime(line[4:-5], "%Y-%m-%d %H:%M:%S.%f")
                if ((datetime.datetime.now() - date).seconds / 60) < minutes:
                    f.writelines(lines[i:])
                    break


def timestamp(f) -> str:
    f.write(f"--- {datetime.datetime.now()} ---\n")


def main() -> None:
    """Asimple wrapper to start `daemon.server` and `daemon.client` with logging.

    Please see dizzy/dizzy/daemon/__main__.py for more info.
    """
    if len(sys.argv) == 2 and sys.argv[1].startswith("-v"):
        client_log_flag = sys.argv[1]
        server_log_flag = client_log_flag
    else:
        client_log_flag = "-vERROR"
        server_log_flag = "-vDEBUG"

    # init logfiles if needbe
    SERVER_LOG = Path("server.log")
    CLIENT_LOG = Path("client.log")
    if not SERVER_LOG.exists():
        SERVER_LOG.touch()
    if not CLIENT_LOG.exists():
        CLIENT_LOG.touch()

    # Start the server
    print("Starting server...")
    prune(SERVER_LOG, PRUNE_MINUTES)
    with open(SERVER_LOG, "a+") as f:
        timestamp(f)

        process = subprocess.Popen(
            ["python", "-m", "dizzy.daemon", "server", server_log_flag],
            stdout=f,
            stderr=f,
        )
        if process.returncode != 0:
            print(
                "Another server may be running... Try dizzy-client if you experience bugs."
            )

    # Start the client
    print("Starting client...")
    prune(CLIENT_LOG, PRUNE_MINUTES)
    with open(CLIENT_LOG, "a+") as f:
        timestamp(f)

        try:
            subprocess.run(
                ["python", "-m", "dizzy.daemon", "client", client_log_flag],
                stderr=f,
            )
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

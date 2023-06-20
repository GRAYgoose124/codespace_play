import datetime
import logging
import subprocess
import sys

from .settings import PRUNE_HOURS


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1].startswith("-v"):
        client_log_flag = sys.argv[1]
        server_log_flag = client_log_flag
    else:
        client_log_flag = "-vERROR"
        server_log_flag = "-vDEBUG"

    # find line in server.log older than 12hr and prune
    with open("server.log", "r") as f:
        lines = f.readlines()

    with open("server.log", "w") as f:
        for i, line in enumerate(lines):
            if line.startswith("--- ") and line.endswith(" ---\n"):
                date = datetime.datetime.strptime(line[4:-5], "%Y-%m-%d %H:%M:%S.%f")
                if ((datetime.datetime.now() - date).seconds / 3600) < PRUNE_HOURS:
                    f.writelines(lines[i:])
                    break

    with open("server.log", "a+") as f:
        f.write(f"--- {datetime.datetime.now()} ---\n")
        subprocess.Popen(
            ["python", "-m", "dizzy.daemon", "server", server_log_flag],
            stdout=f,
            stderr=f,
        )

    subprocess.run(["python", "-m", "dizzy.daemon", "client", client_log_flag])


if __name__ == "__main__":
    main()

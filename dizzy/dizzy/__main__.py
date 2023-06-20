import datetime
import logging
import subprocess
import sys


def main() -> None:
    if len(sys.argv) < 2:
        argv = ""
    else:
        argv = sys.argv[1]

    debug_flag = argv if argv.startswith("-v") else "-vERROR"
    server_log_flag = argv if argv.startswith("-v") else "-vDEBUG"

    with open("server.log", "a+") as f:
        f.write(f"--- {datetime.datetime.now()} ---\n")
        subprocess.Popen(
            ["python", "-m", "dizzy.daemon", "server", server_log_flag],
            stdout=f,
            stderr=f,
        )

    subprocess.run(["python", "-m", "dizzy.daemon", "client", debug_flag])


if __name__ == "__main__":
    main()

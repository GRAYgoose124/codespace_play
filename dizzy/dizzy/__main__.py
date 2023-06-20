import subprocess
from .daemon import server, client


def main() -> None:
    # run server in background and output to file
    with open("server.log", "w") as f:
        subprocess.Popen(["python", "-m", "dizzy.daemon", "server"], stdout=f, stderr=f)

    subprocess.run(["python", "-m", "dizzy.daemon", "client"])


if __name__ == "__main__":
    main()

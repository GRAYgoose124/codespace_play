import zmq
import json
import readline


class SimpleCLIClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def run(self):
        service = "uno"
        task = "A"

        client_ctx = {}

        while True:
            new_service = input(f"Service: ({service}) ")
            service = new_service if new_service else service

            new_task = input(f"Task: ({task}) ")
            task = new_task if new_task else task

            self.socket.send(
                json.dumps(
                    {"service": service, "task": task, "ctx": client_ctx}
                ).encode()
            )

            message = json.loads(self.socket.recv().decode())

            if "ctx" in message:
                # client_ctx = message["ctx"]
                print(f"New context: {message['ctx']}")

            print(message["result" if "result" in message else "error"])

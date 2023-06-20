import json
from pathlib import Path
import zmq

from dizzy import ServiceManager


class RequestServer:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

        self.service_manager = ServiceManager()

    def run(self):
        print("Server running")
        while True:
            message = self.socket.recv()
            print(f"Received request: {message}")

            try:
                json_obj = json.loads(message)
            except json.JSONDecodeError:
                self.socket.send(json.dumps({"error": "Invalid JSON"}).encode())
                continue

            if "service" not in json_obj:
                self.socket.send(
                    json.dumps({"error": "Invalid JSON, no service"}).encode()
                )
                continue

            service = json_obj["service"]

            if service not in self.service_manager.services:
                self.socket.send(json.dumps({"error": "Service not found"}).encode())
                continue

            if "task" not in json_obj:
                self.socket.send(
                    json.dumps({"error": "Invalid JSON, no task"}).encode()
                )
                continue

            task = json_obj["task"]

            try:
                task_obj = self.service_manager.services[service].get_task(task)
            except KeyError:
                self.socket.send(json.dumps({"error": "Task not found"}).encode())
                continue

            try:
                result = task_obj.run()
                self.socket.send(json.dumps({"result": result}).encode())
            except Exception as e:
                self.socket.send(json.dumps({"error": str(e)}).encode())
                continue


class SimpleCLIClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def run(self):
        service = "uno"
        task = "A"

        while True:
            new_service = input(f"Service: ({service}) ")
            service = new_service if new_service else service

            new_task = input("Task: ")
            task = new_task if new_task else "A"

            self.socket.send(json.dumps({"service": service, "task": task}).encode())

            message = json.loads(self.socket.recv().decode())

            print(message)


def server():
    root = Path(__file__).parent
    uno_file = root / "simple_service/uno.yml"

    services = [uno_file]

    server = RequestServer()
    server.service_manager.load_services(services)

    try:
        server.run()
    except KeyboardInterrupt:
        pass


def client():
    client = SimpleCLIClient()

    try:
        client.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    pass

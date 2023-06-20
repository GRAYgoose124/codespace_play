import json
import zmq

from dizzy import ServiceManager


class SimpleRequestServer:
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

            if "ctx" not in json_obj:
                ctx = {}
            else:
                ctx = json_obj["ctx"]

            try:
                result = task_obj.run(ctx)
                self.socket.send(json.dumps({"result": result, "ctx": ctx}).encode())
            except Exception as e:
                self.socket.send(json.dumps({"error": str(e)}).encode())
                continue

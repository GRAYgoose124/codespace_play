import sys
import zmq
import json
import os

if os.name != "nt":
    import readline
import logging

from .settings import data_root


class SimpleCLIClient:
    def __init__(self, address="localhost", port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{address}:{port}")

        self.logger = logging.getLogger(__name__)
        fh = logging.FileHandler(data_root / "client.log")
        fh.setLevel(logging.getLogger().level)
        self.logger.addHandler(fh)

        self.last_request = None

    def run(self):
        client_ctx = {}

        while True:
            command = input("Enter a command (ts/wf/cl/cx/redo/exit): ")
            if command == "ts":
                self.request_task(client_ctx)
            elif command == "wf":
                self.request_workflow(client_ctx)
            elif command == "cl":
                client_ctx = {}
                print("Context cleared.")
            elif command == "cx":
                print(f"Context: {client_ctx}")
            elif command == "redo" or command == "" and self.last_request is not None:
                self.socket.send_json(self.last_request)
                print(f"Sent: {self.last_request}")

                message = json.loads(self.socket.recv().decode())
                print(f"Received: {message}")
            elif command == "exit":
                break
            else:
                print("Invalid command. Please try again.")

    def request_task(self, client_ctx):
        service = input("Enter the common service: ")
        task = input("Enter the task: ")

        self.last_request = {"service": service, "task": task, "ctx": client_ctx}

        self.socket.send_json(self.last_request)

        message = json.loads(self.socket.recv().decode())
        self.logger.debug(f"Received response: {message}")

        if "ctx" in message:
            client_ctx = message["ctx"]
            self.logger.debug(f"\tNew context: {client_ctx}")

        if len(message["errors"]) > 0:
            self.logger.error("\tErrors:")
            for error in message["errors"]:
                if "Service not found" in error:
                    service = None
                self.logger.error(f"\t\t{error}")

        if "available_services" in message:
            self.logger.info(f"\tAvailable tasks: {message['available_services']}")

        print("\tResult: ", message["result"])

    def request_workflow(self, client_ctx):
        entity = input("Enter the entity: ")
        workflow = input("Enter the workflow: ")

        self.last_request = {"entity": entity, "workflow": workflow, "ctx": client_ctx}
        self.socket.send_json(self.last_request)

        message = json.loads(self.socket.recv().decode())
        self.logger.debug(f"Received response: {message}")

        if "ctx" in message:
            client_ctx = message["ctx"]
            self.logger.debug(f"\tNew context: {client_ctx}")

        if len(message["errors"]) > 0:
            self.logger.error("\tErrors:")
            for error in message["errors"]:
                self.logger.error(f"\t\t{error}")

        print("\tResult: ", message["result"])

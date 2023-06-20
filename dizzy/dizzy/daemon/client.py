import zmq
import json
import readline
import logging

logger = logging.getLogger(__name__)


class SimpleCLIClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def run(self):
        client_ctx = {}

        while True:
            command = input("Enter a command (task/workflow/context/clear/exit): ")
            if command == "task":
                self.request_task(client_ctx)
            elif command == "workflow":
                self.request_workflow(client_ctx)
            elif command == "clear":
                client_ctx = {}
                print("Context cleared.")
            elif command == "context":
                print(f"Context: {client_ctx}")
            elif command == "exit":
                break
            else:
                print("Invalid command. Please try again.")

    def request_task(self, client_ctx):
        service = input("Enter the common service: ")
        task = input("Enter the task: ")

        self.socket.send_json({"service": service, "task": task, "ctx": client_ctx})

        message = json.loads(self.socket.recv().decode())
        logger.debug(f"Received response: {message}")

        if "ctx" in message:
            client_ctx = message["ctx"]
            logger.debug(f"\tNew context: {client_ctx}")

        if len(message["errors"]) > 0:
            logger.error("\tErrors:")
            for error in message["errors"]:
                if "Service not found" in error:
                    service = None
                logger.error(f"\t\t{error}")

        if "available_services" in message:
            logger.info(f"\tAvailable tasks: {message['available_services']}")

        print("\tResult: ", message["result"])

    def request_workflow(self, client_ctx):
        entity = input("Enter the entity: ")
        workflow = input("Enter the workflow: ")

        self.socket.send_json(
            {"entity": entity, "workflow": workflow, "ctx": client_ctx}
        )

        message = json.loads(self.socket.recv().decode())
        logger.debug(f"Received response: {message}")

        if "ctx" in message:
            client_ctx = message["ctx"]
            logger.debug(f"\tNew context: {client_ctx}")

        if len(message["errors"]) > 0:
            logger.error("\tErrors:")
            for error in message["errors"]:
                logger.error(f"\t\t{error}")

        print("\tResult: ", message["result"])

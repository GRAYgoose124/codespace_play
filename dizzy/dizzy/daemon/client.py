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
                logger.debug(f"\tNew context: {message['ctx']}")

            if len(message["errors"]) > 0:
                logger.error("\tErrors:")
                for error in message["errors"]:
                    if "Service not found" in error:
                        service = None
                    logger.error(f"\t\t{error}")

            if "available_services" in message:
                logger.info(f"\tAvailable tasks: {message['available_services']}")

            print("\tResult: ", message["result"])

import json
import logging
import zmq

from dizzy import ServiceManager

logger = logging.getLogger(__name__)


class SimpleRequestServer:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

        self.service_manager = ServiceManager()

    def run(self):
        logger.debug("Server running...")
        while True:
            message = self.socket.recv()
            logger.debug(f"Received request: {message}")

            response = {"errors": [], "info": [], "result": None, "ctx": None}
            try:
                json_obj = json.loads(message)
            except json.JSONDecodeError:
                response["errors"].append("Invalid JSON")

            if "service" not in json_obj:
                response["errors"].append("Invalid JSON, no service")
            else:
                service = json_obj["service"]
                if service is None:
                    response["info"].append("Using task with implied service")
                elif service not in self.service_manager.services:
                    response["errors"].append("Service not found")
                else:
                    response["available_services"] = (
                        service,
                        self.service_manager.get_service(service).get_task_names(),
                    )

            if "task" not in json_obj:
                response["errors"].append("Invalid JSON, no task")
            else:
                task = json_obj["task"]
                ctx = json_obj.get("ctx", {})

                try:
                    result = self.service_manager.run_task(task, ctx)
                    response["result"] = result
                    response["ctx"] = ctx
                except Exception as e:
                    response["errors"].append(f"Error running task: {e}")

            out = json.dumps(response).encode()
            logger.debug(f"Sending response: {out}")
            self.socket.send(out)

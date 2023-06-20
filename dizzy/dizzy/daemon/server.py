import json
import logging
import zmq

from dizzy import EntityManager

logger = logging.getLogger(__name__)


class SimpleRequestServer:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

        self.entity_manager = EntityManager()
        self.service_manager = self.entity_manager.service_manager

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
                self.send_response(response)
                continue

            if "entity" in json_obj and json_obj["entity"] is not None:
                self.handle_entity_workflow(json_obj, response)
            elif "service" in json_obj and json_obj["service"] is not None:
                self.handle_service_task(json_obj, response)
            else:
                response["errors"].append("Invalid JSON")

            self.send_response(response)

    def handle_entity_workflow(self, json_obj, response):
        entity = json_obj["entity"]
        workflow = json_obj.get("workflow", None)

        if not workflow:
            response["errors"].append("Invalid JSON, no workflow")
            return

        if entity not in self.entity_manager.entities.keys():
            response["errors"].append("Entity not found")
            return

        response["info"].append(f"Using entity {entity}")
        ctx = self.entity_manager.get_entity(entity).run_workflow(workflow)
        # response["ctx"] = ctx
        # response["completed_workflow"] = workflow
        # response["result"] = ctx["workflow"]["result"]
        response["ctx"] = json_obj.get("ctx", {})
        response["completed_workflow"] = json_obj["workflow"]
        response["result"] = ctx["workflow"]["result"]

    def handle_service_task(self, json_obj, response):
        service = json_obj["service"]
        task = json_obj.get("task", None)

        if not task:
            response["errors"].append("Invalid JSON, no task")
            return

        if service not in self.service_manager.services:
            response["errors"].append("Service not found")
            return

        response["available_services"] = (
            service,
            self.service_manager.get_service(service).get_task_names(),
        )

        ctx = json_obj.get("ctx", {})

        try:
            result = self.service_manager.run_task(task, ctx)
            response["result"] = result
            response["ctx"] = ctx
        except Exception as e:
            response["errors"].append(f"Error running task: {e}")

    def send_response(self, response):
        out = json.dumps(response).encode()
        logger.debug(f"Sending response: {out}")
        self.socket.send(out)

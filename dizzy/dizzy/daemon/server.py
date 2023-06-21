import json
import logging
import zmq

from dizzy import EntityManager
from .settings import common_services, default_entities, data_root


class SimpleRequestServer:
    def __init__(self, address="*", port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{address}:{port}")

        self.logger = logging.getLogger(__name__)
        fh = logging.FileHandler(data_root / "server.log")
        fh.setLevel(logging.getLogger().level)
        self.logger.addHandler(fh)

        self.entity_manager = EntityManager()
        self.service_manager = self.entity_manager.service_manager

        self.service_manager.load_services(common_services.values())
        self.entity_manager.load_entities(default_entities.values())

    def run(self):
        self.logger.debug("Server running...")
        while True:
            message = self.socket.recv()
            self.logger.debug(f"Received request: {message}")

            response = {
                "status": "incomplete",
                "errors": [],
                "info": [],
                "result": None,
                "ctx": None,
            }
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

        response["entity"] = entity
        try:
            ctx = self.entity_manager.get_entity(entity).run_workflow(workflow)
        except KeyError as e:
            response["errors"].append(f"No such workflow: {e}")

        # response["ctx"] = ctx
        response["ctx"] = json_obj.get("ctx", {})
        response["workflow"] = json_obj["workflow"]
        response["status"] = (
            "success" if len(response["errors"]) == 0 else "errored_complete"
        )
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
        self.logger.debug(f"Sending response: {out}")
        self.socket.send(out)

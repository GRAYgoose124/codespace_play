import asyncio
import json
from random import randint
import random
import time
from typing import Any

from .json import JsonPeer

# Note the usage of tasks here refers to taskable peer abilities, not asyncio tasks.


class TaskablePeer(JsonPeer):
    OLD_TASK_THRESHOLD = 30.0

    def __init__(self, *args, group_broadcast_delay=5, **kwargs):
        self.abilities = {}
        self.queue = []
        super().__init__(*args, group_broadcast_delay=group_broadcast_delay, **kwargs)

    def register_ability(self, task: str, handler, overwrite=False):
        """Register a task"""
        if task not in self.abilities or overwrite:
            self.abilities[task] = [handler]
        else:
            self.abilities[task].append(handler)

    def do_abilities(self, data: dict[str, Any]):
        """Complete tasks"""
        todo_abilities = data["todo"].split(";")

        for ability in todo_abilities:
            if data["todo"] in self.abilities:
                for handler in self.abilities[ability]:
                    handler(self, data)
            else:
                self.logger.error(f"Task {ability} not registered")

        data["status"] = "complete"
        data["results"] = f"Task completed by {self.address}"
        self.logger.info(f"Task completed by {self.address}")

        return data

    def remove_from_queue(self, data: dict[str, Any]):
        """Remove a task from the queue"""
        # TODO: UUIDs
        times = enumerate([task["time"] for task in self.queue])
        for i, t in times:
            if t == data["time"]:
                ignored = self.queue.pop(i)
                self.logger.debug(f"Removed task {ignored} from queue")
                break

    def handle_completed_task(self, data: dict[str, Any]):
        """Handle a completed task"""
        if data["sender"] == self.address:
            self.logger.debug(f"Got my completed task back: {data}")
        self.remove_from_queue(data)

    def handle_work(self, data: dict[str, Any]):
        """Handle the workload"""
        # Ignore self-broadcasts
        if data["sender"] == self.address and data["priority"] != self.address:
            return

        # Check if the task is a completed one
        if data["status"] == "complete":
            return self.handle_completed_task(data)

        # Complete old tasks not completed by the priority peer
        if (
            data["status"] == "pending"
            and data["time"] < time.time() - TaskablePeer.OLD_TASK_THRESHOLD
        ):
            data = self.do_abilities(data)
        # If a priority address is given, then that address is the only one that can complete the task.
        # Otherwise, any peer can complete the task.
        elif data["priority"] is None or data["priority"] == self.address:
            data = self.do_abilities(data)
        else:
            data["status"] = "pending"

        self.logger.debug(f"Did work, results:({data}) at {self.address}")

        # Queue the task if it's not complete
        if data["status"] == "pending":
            self.queue.append(data)
        # Check if the complete task is in the queue and remove it if it is.
        elif data["status"] == "complete":
            self.remove_from_queue(data)
            return data

        # broadcast the results
        # await self.broadcast("COMPLETE", json.dumps(data))

    async def workload_wrapper(self) -> str:
        await asyncio.sleep(random.uniform(0.5, 1))
        return await super().workload_wrapper()

    def workload(self) -> dict[str, Any]:
        data = super().workload()
        # get any peer in the group
        peer = list(self.group.keys())[randint(0, len(self.group) - 1)]

        if len(self.queue) > 0:
            data = self.queue[0]
            self.queue.remove(data)
        else:
            data.update(
                {
                    "sender": self.address,
                    "priority": peer,  # or None, if not given any Peer can complete the task and broadcast the results.
                    "todo": None,
                    "status": False,
                    "results": None,
                }
            )

        return data

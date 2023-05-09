import asyncio
import json
from random import randint
import random
import time
from typing import Any

from .json import JsonPeer

# Note the usage of tasks here refers to taskable peer abilities, not asyncio tasks.


class TaskablePeer(JsonPeer):
    def __init__(self, *args, group_broadcast_delay=5, **kwargs):
        self.abilities = {}
        self.queue = []
        super().__init__(*args, group_broadcast_delay=group_broadcast_delay, **kwargs)

    @staticmethod
    def ability(peer, data: dict[str, Any]):
        print(f"TaskablePeer ability called by {peer.address}")
        data["is_complete"] = False
        data["results"] = f"Task queued by {peer.address}"

    def __post_init__(self):
        super().__post_init__()
        self.register_task("taskable", self.ability)

    def register_task(self, task: str, handler, overwrite=False):
        """Register a task"""
        if task not in self.abilities or overwrite:
            self.abilities[task] = [handler]
        else:
            self.abilities[task].append(handler)

    def complete_tasks(self, data: dict[str, Any]):
        """Complete tasks"""
        if data["todo"] in self.abilities:
            for handler in self.abilities[data["todo"]]:
                handler(self, data)
        else:
            self.logger.error(f"Task {data['todo']} not registered")

        data["is_complete"] = True
        data["results"] = f"Task completed by {self.address}"
        self.logger.info(f"Task completed by {self.address}")

    def queue_tasks(self, data: dict[str, Any]):
        """Queue tasks"""
        self.queue.append(data)

    def handle_work(self, data: dict[str, Any]):
        """Handle the workload"""
        # Ignore self-broadcasts
        if data["sender"] == self.address:
            return

        self.logger.debug(f"Got work ({data})")

        # Check if the task is in the queue
        # TODO: UUIDs
        if data["is_complete"]:
            if data["time"] in [task["time"] for task in self.queue]:
                self.queue.remove(data)
        elif data["priority"] != self.address and not data["time"] < time.time() - 10.0:
            # Complete old tasks not completed by the priority peer
            self.complete_tasks(data)
            return

        # Ignore any complete work that isn't for this peer
        if data["is_complete"] and data["priority"] != self.address:
            return

        # If a priority address is given, then that address is the only one that can complete the task.
        # Otherwise, any peer can complete the task.
        if data["priority"] is None or data["priority"] == self.address:
            self.complete_tasks(data)
        else:
            # If the task is not complete, then add it to the queue and wait to see if the priority peer completes it.
            pass

        # Queue the task if it's not complete
        if not data["is_complete"]:
            self.queue_tasks(data)

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
                    "todo": "taskable",
                    "is_complete": False,
                    "results": None,
                }
            )

        return data

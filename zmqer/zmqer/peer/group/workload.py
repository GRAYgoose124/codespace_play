from abc import abstractmethod, ABCMeta
import json

from . import GroupPeer


class WorkloadPeer(GroupPeer, metaclass=ABCMeta):
    def register_message_type(self, message_type, handler, overwrite=False):
        self.__workload_type = message_type
        return super().register_message_type(message_type, handler, overwrite)

    @abstractmethod
    async def workload_wrapper(self):
        pass

    async def broadcast_loop(self):
        while not self.done:
            try:
                data = await getattr(self, "workload_wrapper")()
                await self.broadcast(self.__workload_type, data)
            except Exception as e:
                self.logger.error(f"Error: {e}")

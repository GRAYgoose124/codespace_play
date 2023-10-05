import asyncio
from abc import ABC, abstractmethod


class LoadingIndicator(ABC):
    """Abstract base class for loading indicators."""

    def __init__(self, interval=0.05):
        """
        Creates a loading indicator object.

        Args:
            interval (float): Time interval in seconds between each step of the loading indicator.
        """
        self.interval = interval
        self.counter = 0
        self.is_done = False

    @abstractmethod
    async def run(self):
        """Runs the loading indicator."""
        pass

    def done(self):
        """Signals that the loading indicator is done."""
        self.is_done = True


def progress(indicator):
    """Decorator to wrap a coroutine function with the LoadingIndicator run function."""

    def wrapped_callback(callback):
        async def wrapped(*args, **kwargs):
            result = await callback(*args, **kwargs)
            indicator.done()
            return result

        async def new_callback(*args, **kwargs):
            run_task = asyncio.create_task(indicator.run())
            wrapped_task = asyncio.create_task(wrapped(*args, **kwargs))
            done, pending = await asyncio.wait(
                {run_task, wrapped_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                await task
            return next(iter(done)).result()

        return new_callback

    return wrapped_callback

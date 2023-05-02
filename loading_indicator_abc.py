import asyncio
import signal
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


class BrailleLoadingIndicator(LoadingIndicator):
    """Displays a loading indicator in the CLI using Unicode Braille characters."""
    def __init__(self, br_dots=None, done_callback=None, step_callback=None, **kwargs):
        """
        Creates a BrailleLoadingIndicator object.

        Args:
            br_dots (list of str): List of Unicode Braille characters to use for the loading indicator.
                Defaults to the standard set of characters.
            done_callback (callable): Callback function to call when the loading indicator is done.
                Defaults to printing the number of steps taken.
            step_callback (callable): Callback function to call on each step of the loading indicator.
                Defaults to printing the Braille character for the current step.
            **kwargs: Additional arguments to pass to the parent class constructor.
        """
        super().__init__(**kwargs)
        self.br_dots = br_dots or ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.done_callback = done_callback or self.default_done_callback
        self.step_callback = step_callback or self.default_step_callback

    async def run(self):
        """Runs the loading indicator."""
        while not self.is_done:
            self.step_callback(self.br_dots[self.counter % len(self.br_dots)])
            self.counter += 1
            await asyncio.sleep(self.interval)
        self.done_callback(self.counter)

    @staticmethod
    def default_step_callback(braille_char):
        """Default step callback function that prints the Braille character for the current step."""
        print("\r" + braille_char, end="")

    @staticmethod
    def default_done_callback(num_steps):
        """Default done callback function that prints the number of steps taken."""
        print(f"\nDone after {num_steps} steps.")


def progress(indicator):
    """Decorator to wrap a coroutine function with the LoadingIndicator run function."""
    def wrapped_callback(callback):
        async def wrapped():
            result = await callback()
            indicator.done()
            return result

        async def new_callback():
            run_task = asyncio.create_task(indicator.run())
            wrapped_task = asyncio.create_task(wrapped())
            done, pending = await asyncio.wait({run_task, wrapped_task}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                await task
            return next(iter(done)).result()

        return new_callback

    return wrapped_callback


async def main():
    try:
        # Customize the loading indicator with custom callbacks
        def custom_done_callback(num_steps):
            print(f"\nFinished after {num_steps} steps!")

        def custom_step_callback(braille_char):
            print(f"\rStep: {braille_char}", end="")

        indicator = BrailleLoadingIndicator(done_callback=custom_done_callback)#, step_callback=custom_step_callback)

        # Add a signal handler to the event loop to catch keyboard interrupts
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, indicator.done)

        # Define a coroutine function that simulates some long-running task
        @progress(indicator)
        async def my_task():
            await asyncio.sleep(1)
            return "Task result"

        # Wrap the coroutine function with the progress decorator

        # Run the decorated task
        result = await my_task()
        print(f"\nTask result: {result}")
        
    finally:
        # Remove the signal handler when the program is done
        loop.remove_signal_handler(signal.SIGINT)


if __name__ == "__main__":
    asyncio.run(main())

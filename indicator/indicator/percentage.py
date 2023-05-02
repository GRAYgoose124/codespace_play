import asyncio
from .indicator import LoadingIndicator


class PercentageLoadingIndicator(LoadingIndicator):
    """Displays a loading indicator in the CLI as a percentage."""
    def __init__(self, max_value, done_callback=None, step_callback=None, **kwargs):
        """
        Creates a PercentageLoadingIndicator object.

        Args:
            max_value (int): The maximum value of the loading indicator.
            done_callback (callable): Callback function to call when the loading indicator is done.
                Defaults to printing the percentage as a string.
            step_callback (callable): Callback function to call on each step of the loading indicator.
                Defaults to printing the percentage as a string.
            **kwargs: Additional arguments to pass to the parent class constructor.
        """
        super().__init__(**kwargs)
        self.max_value = max_value
        self.done_callback = done_callback or self.default_done_callback
        self.step_callback = step_callback or self.default_step_callback

    async def run(self):
        """Runs the loading indicator."""
        while not self.is_done:
            percentage = int((self.counter / self.max_value) * 100)
            self.step_callback(percentage)
            self.counter += 1
            await asyncio.sleep(self.interval)
        self.done_callback(percentage)

    @staticmethod
    def default_step_callback(percentage):
        """Default step callback function that prints the percentage as a string."""
        print(f"\r{percentage}%", end="")

    @staticmethod
    def default_done_callback(percentage):
        """Default done callback function that prints the percentage as a string."""
        print(f"\nDone at {percentage}%.")




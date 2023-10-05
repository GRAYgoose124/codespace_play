import asyncio
from .indicator import LoadingIndicator


class SpinnerLoadingIndicator(LoadingIndicator):
    """Displays a loading indicator in the CLI as a spinner animation."""

    def __init__(
        self, spinner_chars=None, done_callback=None, step_callback=None, **kwargs
    ):
        """
        Creates a SpinnerLoadingIndicator object.

        Args:
            spinner_chars (list of str): List of characters to use for the spinner animation.
                Defaults to the standard set of characters.
            done_callback (callable): Callback function to call when the loading indicator is done.
                Defaults to printing a message indicating completion.
            step_callback (callable): Callback function to call on each step of the loading indicator.
                Defaults to printing the spinner character for the current step.
            **kwargs: Additional arguments to pass to the parent class constructor.
        """
        super().__init__(**kwargs)
        self.spinner_chars = spinner_chars or ["-", "\\", "|", "/"]
        self.done_callback = done_callback or self.default_done_callback
        self.step_callback = step_callback or self.default_step_callback

    async def run(self):
        """Runs the loading indicator."""
        while not self.is_done:
            self.step_callback(
                self.spinner_chars[self.counter % len(self.spinner_chars)]
            )
            self.counter += 1
            await asyncio.sleep(self.interval)
        self.done_callback(self.counter)

    @staticmethod
    def default_step_callback(spinner_char):
        """Default step callback function that prints the spinner character for the current step."""
        print(f"\r{spinner_char}", end="")

    @staticmethod
    def default_done_callback():
        """Default done callback function that prints a message indicating completion."""
        print("\nDone.")

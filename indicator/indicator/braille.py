import asyncio

from .indicator import LoadingIndicator


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
import asyncio
import signal


class LoadingIndicator:
    """Displays a loading indicator in the CLI using Unicode Braille characters."""
    def __init__(self, br_dots=None):
        """
        Creates a loading indicator object.

        Args:
            br_dots (list of str): List of Unicode Braille characters to use for the loading indicator.
                Defaults to the standard set of characters.
        """
        self.br_dots = br_dots or ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.counter = 0
        self.is_done = False

    def reset(self):
        """Resets the loading indicator."""
        self.counter = 0
        self.is_done = False

    async def run(self):
        """Runs the loading indicator."""
        while not self.is_done:
            print("\r" + self.br_dots[self.counter % len(self.br_dots)], end="")
            self.counter += 1
            await asyncio.sleep(0.1)

    def done(self):
        """Signals that the loading indicator is done."""
        self.is_done = True


def progress(indicator):
    """Decorator to wrap a coroutine function with the LoadingIndicator run function."""
    def wrapped_callback(callback):
        async def wrapped():
            await callback()
            indicator.done()

        async def new_callback():
            await asyncio.gather(indicator.run(), wrapped())
            
        return new_callback
    return wrapped_callback


async def main():
    try:
        # Customize the loading indicator
        moon_phases = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
        indicator = LoadingIndicator(moon_phases)

        # Add a signal handler to the event loop to catch keyboard interrupts
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, indicator.done)

        @progress(indicator)
        async def my_task():
            await asyncio.sleep(2)

        # Run the decorated task
        await my_task()

    finally:
        # Remove the signal handler when the program is done
        loop.remove_signal_handler(signal.SIGINT)
        print(f"\nDone after {indicator.counter} steps.")


if __name__ == "__main__":
    asyncio.run(main())
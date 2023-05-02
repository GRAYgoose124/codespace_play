import asyncio


class LoadingIndicator:
    """Displays a loading indicator in the CLI using Unicode Braille characters."""
    br_dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self):
        """Creates a loading indicator object."""
        self.counter = 0
        self.is_done = False

    def reset(self):
        """Resets the loading indicator."""
        self.counter = 0
        self.is_done = False

    async def run(self):
        """Runs the loading indicator."""
        while not self.is_done:
            print("\r" + self.br_dots[self.counter % 10], end="")
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
        indicator = LoadingIndicator()

        @progress(indicator)
        async def my_task():
            await asyncio.sleep(1)

        # Run the decorated task
        await my_task()

    except KeyboardInterrupt:
        indicator.done()
    finally:
        print(f"\nDone after after {indicator.counter} steps.")



if __name__ == "__main__":
    asyncio.run(main())

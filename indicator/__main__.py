import asyncio
import signal

from abc_indicator import BrailleLoadingIndicator, PercentageLoadingIndicator, SpinnerLoadingIndicator
from abc_indicator import progress


async def main():
    try:
        # Customize the loading indicator with custom callbacks
        def custom_done_callback(num_steps):
            print(f"\nFinished after {num_steps} steps!")

        def custom_step_callback(braille_char):
            print(f"\rStep: {braille_char}", end="")

        # indicator = BrailleLoadingIndicator(done_callback=custom_done_callback)#, step_callback=custom_step_callback)
        # indicator = PercentageLoadingIndicator(20, done_callback=custom_done_callback)#, step_callback=custom_step_callback)
        indicator = SpinnerLoadingIndicator(done_callback=custom_done_callback)#, step_callback=custom_step_callback)
        
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
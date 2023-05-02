import time


def loading_indicator(done_callback=lambda: False, step_callback=lambda: time.sleep(0.1)):
    """Displays a loading indicator in the CLI using Unicode Braille characters."""
    br_dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    i = 0
    while not done_callback():
        print("\r" + br_dots[i % 10], end="")
        step_callback()
        i += 1


g_counter = 0
step_complete = False
def main():
    def long_running_step():
        global step_complete
        global g_counter

        if step_complete:
            g_counter += 1
            step_complete = False

    def long_running_function():
        global step_complete
        for i in range(10):
            long_running_step()
            time.sleep(0.05)
            step_complete = True

    try:
        loading_indicator(done_callback=long_running_function, step_callback=long_running_step)
    except KeyboardInterrupt:
        print(f"\n\nInterrupted after {g_counter} steps.")


if __name__ == "__main__":
    main()
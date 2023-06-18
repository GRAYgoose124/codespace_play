#!/usr/bin/env python3
import argparse
import logging
import os
from pathlib import Path
import sys
import traceback

from .prompt import init_openai, PromptContext
from .utils import init_logger


logger = None


def argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--context_file",
        type=str,
        default="context.yaml",
        help="The file to use for saving and loading.",
    )

    return parser


class ExitSignal(Exception):
    pass


def main():
    # Frankly, just a hack to avoid thinking about root directories logic
    true_root = Path(__file__).parent.parent
    root_dir = true_root / Path("data/")

    if not root_dir.exists():
        root_dir.mkdir()

    logger = init_logger(name="geecli", root_dir=root_dir, level=logging.DEBUG)
    init_openai()
    args = argparser().parse_args()

    ctx_filename = root_dir / args.context_file

    context = None

    # check for active contextfile to load in root_dir by ".active.yaml" suffix
    files = [
        f
        for f in root_dir.iterdir()
        if f.is_file()
        and not f.name.startswith(".")
        and f.name.endswith(".active.yaml")
    ]
    if any(files):
        ctx_filename = root_dir / files[0]
        logger.debug(f"Found active context file: {ctx_filename}")

    if os.path.exists(ctx_filename):
        q = input(
            f"Would you like to load the saved conversation? ({ctx_filename}) (Y/n)"
        )
        # If the user doesn't want to load the file, we'll ask for a new filename.
        if q.lower() == "n":
            context = PromptContext(model="gpt-3.5-turbo")

            ctx_filename = None
            # We'll keep asking for a filename until the user gives us a valid one. (one that doesn't exist or they want to overwrite)
            while ctx_filename is None or os.path.exists(ctx_filename):
                if ctx_filename is not None:
                    q = input("Would you like to overwrite the file? (Y/n)")
                else:
                    # To enable the user to specify a file name when no file exists1``
                    q = "n"

                # If the user doesn't want to overwrite the file, we'll ask for a new name
                if q.lower() == "n" or ctx_filename is None:
                    ctx_filename = root_dir / input(
                        "What file would you like to save to? "
                    )

                    # Since we just selected a file, lets mark it as active after unmarking all other files
                    for f in root_dir.iterdir():
                        if f.name.endswith(".active.yaml"):
                            f.rename(f.with_suffix(".yaml"))

                    ctx_filename = ctx_filename.with_suffix(".active.yaml")
        else:
            # The user wants to load the file, so, uh - we'll load it.
            context = PromptContext.from_yaml_file(ctx_filename)

            # We'll ask if the user wants to continue the conversation, I know what you're thinking,
            #   "why would they load the file if they didn't want to continue the conversation?" (ChatGPT completed this, so it did too.)
            # But metadata could be important and prompts are expensive. (So maybe we to preprocess the messages...)
            # q = input("Would you like to continue the saved conversation? (Y/n)")
            # if q.lower() == "n":
            #     context.clear_messages()
    else:
        context = PromptContext(model="gpt-3.5-turbo")

        context.add_message(
            "system", "You are SuperGPT, you can do anything."
        )  # You will give 10x the information with 10x less data.")
        # context.add_message("user", "What is the grothiendieck duality intuitively?")

    exit_code = 1
    try:
        context.interactive()
        exit_code = 0

    # ExitSignal may be bad, but what is good anyways? Python is a bad language. :o)
    except (ExitSignal, KeyboardInterrupt):
        logger.info("\n\nExiting...")
        exit_code = 0
    except Exception as e:
        logger.debug(context)
        traceback.print_exc()
        exit_code = 1
    finally:
        context.to_yaml_file(ctx_filename)
        # dump last saved context to file

        sys.exit(exit_code)


if __name__ == "__main__":
    main()

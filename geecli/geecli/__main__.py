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


def interactive_loop(ctx: PromptContext) -> None:
    while True:
        new_message = input("You: ")

        if len(new_message) == 0:
            continue

        if new_message[0] == "/":
            match new_message[1:]:
                case "exit":
                    return
                case "tokens":
                    print(f"Total tokens used: {ctx.total_tokens_used}")
                    pass
                case "cost":
                    ctx.logger.debug(
                        f"Prompting with "
                        "\n".join([m["content"] for m in ctx.messages])
                    )
                    print(f"You will spend {ctx.total_tokens_used} tokens.")
                    pass
                case "messages":
                    print("\n".join([m["content"] for m in ctx.messages]))
                case "clear":
                    q = input("THIS IS A VERY DESTRUCTIVE ACTION, ARE YOU SURE? (y/N)")
                    if q.lower() == "y":
                        # backup
                        date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                        ctx.to_yaml_file(f"backup-{date}.yaml")
                        ctx.clear_messages()
                        print("Prompt messages cleared, fresh working space ready.")
                case "open":
                    files = os.listdir(os.getcwd())
                    for i, yaml in enumerate(files):
                        if yaml.endswith(".yaml"):
                            name_only = yaml.split(".")[0]
                            print(f"{i}: {name_only}")
                    index = int(input("Which file to open? "))
                    ctx.from_yaml_file(files[index])
                    print(f"Loaded {files[index]}")
                case "save":
                    name = input("Name of the file? ")
                    ctx.to_yaml_file(name)

            continue

        try:
            response = ctx.prompt(new_message)
        except Exception as e:
            ctx.logger.error("Error during prompting:", e)
            traceback.print_exc()
            continue

        print(f"{ctx.model}: ", response["choices"][0]["message"]["content"])


def load_ctx_wizard(ctx_filename: Path) -> PromptContext:
    data_dir = ctx_filename.parent

    # check for active contextfile to load in root_dir by ".active.yaml" suffix
    files = [
        f
        for f in data_dir.iterdir()
        if f.is_file()
        and not f.name.startswith(".")
        and f.name.endswith(".active.yaml")
    ]
    if any(files):
        ctx_filename = data_dir / files[0]
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
                    ctx_filename = data_dir / input(
                        "What file would you like to save to? "
                    )

                    # Since we just selected a file, lets mark it as active after unmarking all other files
                    for f in data_dir.iterdir():
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

    return context


def main():
    # args and openai setup
    init_openai()
    args = argparser().parse_args()

    # root
    root = Path(__file__).parent.parent
    data_dir = root / Path("data/")
    if not data_dir.exists():
        data_dir.mkdir()

    # logging
    global logger
    logger = init_logger(name="geecli", root_dir=data_dir, level=logging.INFO)

    # context
    ctx_filename = data_dir / args.context_file
    context = load_ctx_wizard(ctx_filename)

    if len(context.messages) == 0:
        context.add_message(
            "system", "You are SuperGPT, you can do anything."
        )  # You will give 10x the information with 10x less data.")

    # main loop
    exit_code = 1
    try:
        interactive_loop(context)
        exit_code = 0
    except (ExitSignal, KeyboardInterrupt):
        logger.info("Exiting...")
        exit_code = 0
    except Exception as e:
        logger.debug(context)
        traceback.print_exc()
        exit_code = 1
    finally:
        context.to_yaml_file(ctx_filename)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

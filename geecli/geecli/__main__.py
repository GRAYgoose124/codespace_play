#!/usr/bin/env python3
import datetime
import logging
import os
from pathlib import Path
import sys
import traceback

from .prompt import init_openai, PromptContext
from .utils import init_logger, ExitSignal, argparser


logger = None


def interactive_loop(ctx: PromptContext) -> None:
    while True:
        new_message = input("You: ")

        if len(new_message) == 0:
            continue

        if new_message[0] == "/":
            match new_message[1:]:
                case "exit":
                    return 0
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
        else:
            try:
                response = ctx.prompt(new_message)
                print(f"{ctx.model}: ", response["choices"][0]["message"]["content"])

            except Exception as e:
                ctx.logger.error("Error during prompting:", e)
                traceback.print_exc()


def load_ctx_wizard(default_ctx_path: Path) -> PromptContext:
    data_dir = default_ctx_path.parent

    # check for active contextfile to load in root_dir by ".active.yaml" suffix
    files = [
        f
        for f in data_dir.iterdir()
        if f.is_file()
        and not f.name.startswith(".")
        and f.name.endswith(".active.yaml")
    ]
    if any(files):
        default_ctx_path = data_dir / files[0]
        logger.debug(f"Found active context file: {default_ctx_path}")

    if os.path.exists(default_ctx_path):
        q = input(
            f"Would you like to load the saved conversation? ({default_ctx_path}) (Y/n)"
        )
        # If the user doesn't want to load the file, we'll ask for a new filename.
        if q.lower() == "n":
            context = PromptContext(model="gpt-3.5-turbo", save_path=str(data_dir))

            default_ctx_path = None
            # We'll keep asking for a filename until the user gives us a valid one. (one that doesn't exist or they want to overwrite)
            while default_ctx_path is None or os.path.exists(default_ctx_path):
                if default_ctx_path is not None:
                    q = input("Would you like to overwrite the file? (Y/n)")
                else:
                    # To enable the user to specify a file name when no file exists.
                    q = "n"

                # If the user doesn't want to overwrite the file, we'll ask for a new name
                if q.lower() == "n" or default_ctx_path is None:
                    default_ctx_path = data_dir / input(
                        "What file would you like to save to? "
                    )

                    # Since we just selected a file, lets mark it as active after unmarking all other files
                    for f in data_dir.iterdir():
                        if f.name.endswith(".active.yaml"):
                            f.rename(f.with_suffix(".yaml"))

                    default_ctx_path = default_ctx_path.with_suffix(".active.yaml")
        else:
            context = PromptContext.load(default_ctx_path)
    else:
        context = PromptContext(model="gpt-3.5-turbo", save_path=str(data_dir))

    return context


def main():
    # init
    #   args and openai setup
    init_openai()
    args = argparser().parse_args()

    #   root
    root = Path(__file__).parent.parent
    data_dir = root / Path("data/")
    if not data_dir.exists():
        data_dir.mkdir()

    #   logging
    global logger
    logger = init_logger(name="geecli", root_dir=data_dir, level=logging.INFO)

    #   context
    context = load_ctx_wizard(data_dir / args.context_file)

    # main loop
    try:
        exit_code = interactive_loop(context)
    except (ExitSignal, KeyboardInterrupt):
        logger.info("Exiting...")
        exit_code = 0
    except Exception as e:
        logger.debug(context)
        traceback.print_exc()
        exit_code = 1
    finally:
        context.save()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

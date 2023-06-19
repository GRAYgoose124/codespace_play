#!/usr/bin/env python3
import datetime
import logging
import os
from pathlib import Path
import sys
import traceback

from .prompt import init_openai, PromptContext
from .binmanager import PromptBinManager as BinManager
from .utils import init_logger, ExitSignal, argparser


logger = None


def interactive_loop(ctx: PromptContext) -> None:
    import readline

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
                    print(f"You have spent {ctx.total_tokens_used} tokens.")
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

                case "binman":
                    print("Welcome to BinManager!")
                    with BinManager(ctx.save_path) as bm:
                        bm.interactive_loop()

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

                    default_ctx_path = default_ctx_path.with_suffix(".active.yaml")
        else:
            context = PromptContext.load(default_ctx_path.with_suffix(".yaml"))
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

    # get active context file
    if (
        input(f"Would you like to load the last saved conversation? (Y/n)").lower()
        != "n"
    ):
        active_files = [
            f
            for f in data_dir.iterdir()
            if f.is_file()
            and not f.name.startswith(".")
            and f.name.endswith(".active.yaml")
        ]
        if any(active_files):
            default_ctx_path = data_dir / active_files[0]
            logger.debug(f"Found active context file: {default_ctx_path}")
            context = PromptContext.load(default_ctx_path)
        else:
            context = PromptContext(save_path=str(data_dir))
    else:
        context = PromptContext(save_path=str(data_dir))

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
        if len(context.messages) > 0:
            # unmark other active files
            for f in data_dir.iterdir():
                if ".active." in f.name:
                    f.rename(f.with_name(f.name.replace(".active.", ".")))

            path = context.save()

            # mark active file
            if not path.name.endswith(".active.yaml"):
                path.rename(path.with_suffix(".active.yaml"))

            logger.debug(f"Saved context to {path}")

        sys.exit(exit_code)


if __name__ == "__main__":
    main()

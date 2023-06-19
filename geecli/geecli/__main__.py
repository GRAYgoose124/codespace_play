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

from .cmdli import CLI


logger = None


def interactive_loop(ctx: PromptContext) -> None:
    class GeeCLI(CLI):
        @staticmethod
        @CLI.command
        def contx():
            for k, v in ctx.__dict__.items():
                print(f"{k}: {v}")

        @staticmethod
        @CLI.command
        def tokens():
            print(f"Total tokens used: {ctx.total_tokens_used}")
            pass

        @staticmethod
        @CLI.command
        def cost():
            ctx.logger.debug(
                f"Prompting with "
                "\n".join([m["content"] for m in ctx.messages_to_prompt])
            )
            print(
                f"You have spent {ctx.total_tokens_used} tokens. You will spend an average of {len(ctx.messages_to_prompt) / 4} tokens next prompting."
            )
            pass

        @staticmethod
        @CLI.command
        def messages():
            print("\n".join([m["content"] for m in ctx.messages]))

        @staticmethod
        @CLI.command
        def clear():
            q = input("THIS IS A VERY DESTRUCTIVE ACTION, ARE YOU SURE? (y/N)")
            if q.lower() == "y":
                # backup
                date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                ctx.to_yaml_file(f"backup-{date}.yaml")
                ctx.clear_messages()
                print("Prompt messages cleared, fresh working space ready.")

        @staticmethod
        @CLI.command
        def open():
            files = os.listdir(os.getcwd())
            for i, yaml in enumerate(files):
                if yaml.endswith(".yaml"):
                    name_only = yaml.split(".")[0]
                    print(f"{i}: {name_only}")
            index = int(input("Which file to open? "))
            ctx.from_yaml_file(files[index])
            print(f"Loaded {files[index]}")

        @staticmethod
        @CLI.command
        def save():
            name = input("Name of the file? ")
            ctx.to_yaml_file(name)

        @staticmethod
        @CLI.command
        def binman():
            print("Welcome to BinManager!")
            with BinManager(ctx.save_path) as bm:
                bm.interactive_loop()

        @staticmethod
        @CLI.not_slash
        def prompt_handler(new_message: str):
            try:
                response = ctx.prompt(new_message)
                print(f"{ctx.model}: ", response["choices"][0]["message"]["content"])
            except Exception as e:
                ctx.logger.error("Error during prompting:", e)
                traceback.print_exc()

    cli = GeeCLI()
    cli.loop()


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

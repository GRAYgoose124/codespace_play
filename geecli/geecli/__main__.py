#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import sys
import traceback
import openai

from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard
from typing import Literal

import logging


logger = None


def init_openai():
    OPEN_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPEN_API_KEY is None:
        print("No OPENAI_API_KEY env variable found, using ~/.openApI_key")

        with open(os.path.expanduser("~/.openApI_key")) as f:
            access = f.read().strip()
    else:
        access = OPEN_API_KEY
    openai.api_key = access


def init_logger(root_dir: Path = Path(__file__).parent.parent, level=logging.INFO):
    logging.basicConfig(level=level)
    global logger
    logger = logging.getLogger(__name__)
    # add file handler
    fh = logging.FileHandler(root_dir / "debug.log")
    fh.setLevel(level)
    logger.addHandler(fh)


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


@dataclass
class PromptContext(YAMLWizard):
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 8000

    messages: list[dict[str, str]] = field(default_factory=list)
    total_tokens_used: int = 0

    # api_history: list[dict] = field(default_factory=list)

    def add_message(
        self, role: Literal["system", "user", "assistant"], content: str
    ) -> None:
        self.messages.append({"role": role, "content": content[: self.max_tokens]})

    def remove_message(self, index: int) -> None:
        self.messages.pop(index)

    def clear_messages(self) -> None:
        self.messages = []

    def delete_messages_by_ids(self, ids: list[int]) -> None:
        for i in ids:
            self.remove_message(i)

    def get_messages_by_role(
        self, role: Literal["system", "user", "assistant"], invert: bool = True
    ) -> dict[str, str]:
        return [m for m in self.messages if m["role"] == role][:: -1 if invert else 1]

    def get_message_by_index(self, index: int, invert: bool = True) -> dict[str, str]:
        return self.messages[-index if invert else index]

    def get_last_message(self) -> dict[str, str]:
        return self.get_message_by_index(0)

    def get_last_user_message(self) -> dict[str, str]:
        return self.get_messages_by_role("user")[0]

    def get_last_system_message(self) -> dict[str, str]:
        return self.get_messages_by_role("system")[0]

    def get_last_assistant_message(self) -> dict[str, str]:
        return self.get_messages_by_role("assistant")[0]

    def get_used_tokens(self) -> int:
        return sum([m["usage"]["total_tokens"] for m in self.api_history])

    def prompt(self, new_message) -> dict:
        self.add_message("user", new_message)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.messages
        )

        message = response.choices[0].message.to_dict()

        logger.debug(response)

        self.total_tokens_used += response.usage.total_tokens

        # self.api_history.append(response)
        self.messages.append(message)

        return response

    def interactive(self) -> None:
        while True:
            new_message = input("You: ")

            match new_message:
                case "exit":
                    return
                case "":
                    continue
                case "TOKENS":
                    print(f"Total tokens used: {self.total_tokens_used}")
                    continue
                case "TO_BE_PROMPTED":
                    print(
                        f"Prompting with "
                        "\n".join([m["content"] for m in self.messages])
                    )
                    continue

            try:
                response = self.prompt(new_message)
            except Exception as e:
                logger.error("Error during prompting:", e)
                traceback.print_exc()
                continue

            print(f"{self.model}: ", response["choices"][0]["message"]["content"])

    def __repr__(self) -> str:
        return f"<PromptContext model={self.model} messages={len(self.messages)}>"

    def __str__(self) -> str:
        return f"{self.get_used_tokens()=}\nMessaging with {self.model}:\n" + "\n".join(
            [
                f"{m['choices'][0]['message']['role']}: {m['choices'][0]['message']['content']}"
                for m in self.api_history
            ]
        )


def main():
    # Frankly, just a hack to avoid thinking about root directories logic
    true_root = Path(__file__).parent.parent
    root_dir = true_root / Path("data/")

    if not root_dir.exists():
        root_dir.mkdir()

    init_logger(root_dir)
    init_openai()
    args = argparser().parse_args()

    ctx_filename = root_dir / args.context_file

    context = None

    if os.path.exists(ctx_filename):
        q = input("Would you like to load the saved conversation? (Y/n)")
        if q.lower() == "n":
            context = PromptContext(model="gpt-3.5-turbo")

            ctx_filename = None
            while ctx_filename is None or os.path.exists(ctx_filename):
                if ctx_filename is not None:
                    q = input("Would you like to overwrite the file? (Y/n)")
                else:
                    # To enable the user to specify a file name when no file exists
                    q = "n"

                if q.lower() == "n" or ctx_filename is None:
                    ctx_filename = root_dir / input(
                        "What file would you like to save to? "
                    )
                    if not ctx_filename.suffix:
                        ctx_filename = ctx_filename.with_suffix(".yaml")

        else:
            context = PromptContext.from_yaml_file(ctx_filename)

            q = input("Would you like to continue the saved conversation? (Y/n)")
            if q.lower() == "n":
                context.clear_messages()
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

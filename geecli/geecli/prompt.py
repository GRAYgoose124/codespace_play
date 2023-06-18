import datetime
import logging
import os
import traceback
import openai

from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard
from typing import Literal

from .utils import init_logger


def init_openai():
    OPEN_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPEN_API_KEY is None:
        print("No OPENAI_API_KEY env variable found, using ~/.openApI_key")

        with open(os.path.expanduser("~/.openApI_key")) as f:
            access = f.read().strip()
    else:
        access = OPEN_API_KEY
    openai.api_key = access


@dataclass
class PromptContext(YAMLWizard):
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 8000

    messages: list[dict[str, str]] = field(default_factory=list)
    total_tokens_used: int = 0

    # api_history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.logger = init_logger(
            name=self.__class__.__name__, parent="geecli", level=logging.INFO
        )

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

        self.logger.debug(response)

        self.total_tokens_used += response.usage.total_tokens

        # self.api_history.append(response)
        self.messages.append(message)

        return response

    def interactive(self) -> None:
        while True:
            new_message = input("You: ")

            if len(new_message) == 0:
                continue

            if new_message[0] == "/":
                match new_message[1:]:
                    case "exit":
                        return
                    case "tokens":
                        print(f"Total tokens used: {self.total_tokens_used}")
                        pass
                    case "cost":
                        self.logger.debug(
                            f"Prompting with "
                            "\n".join([m["content"] for m in self.messages])
                        )
                        print(f"You will spend {self.total_tokens_used} tokens.")
                        pass
                    case "messages":
                        print("\n".join([m["content"] for m in self.messages]))
                    case "clear":
                        q = input(
                            "THIS IS A VERY DESTRUCTIVE ACTION, ARE YOU SURE? (y/N)"
                        )
                        if q.lower() == "y":
                            # backup
                            date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                            self.to_yaml_file(f"backup-{date}.yaml")
                            self.clear_messages()
                            print("Prompt messages cleared, fresh working space ready.")
                    case "open":
                        files = os.listdir(os.getcwd())
                        for i, yaml in enumerate(files):
                            if yaml.endswith(".yaml"):
                                name_only = yaml.split(".")[0]
                                print(f"{i}: {name_only}")
                        index = int(input("Which file to open? "))
                        self.from_yaml_file(files[index])

                continue

            try:
                response = self.prompt(new_message)
            except Exception as e:
                self.logger.error("Error during prompting:", e)
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

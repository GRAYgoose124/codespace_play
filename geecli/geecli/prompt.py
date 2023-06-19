import datetime
import logging
import os
from pathlib import Path
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
    title: str = "Conversation"
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000

    messages: list[dict[str, str]] = field(default_factory=list)
    total_tokens_used: int = 0

    save_path: str = field(default=".")

    # api_history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self._saved_file = None
        self.logger = init_logger(
            name=self.__class__.__name__,
            parent="geecli",
            level=logging.INFO,
            root_dir=Path(self.save_path),
        )

    @staticmethod
    def load(filename: Path) -> "PromptContext":
        ctx = PromptContext.from_yaml_file(filename)
        ctx._saved_file = filename
        ctx.save_path = str(filename.parent)
        ctx.logger.info(f"Loaded context from {filename}")

        return ctx

    def save(self, filename: Path = None) -> Path:
        if filename is not None:
            self._saved_file = filename

        if self._saved_file is None:
            self._saved_file = (
                Path(self.save_path) / f"{self.title}-{datetime.datetime.now()}"
            ).with_suffix(".yaml")

        if self._saved_file.exists():
            self.logger.info(f"Overwriting {self.save_path}")

        self.to_yaml_file(self._saved_file)
        self.logger.info(f"Saved context to {self._saved_file}")

        return self._saved_file

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
    ) -> list[dict[str, str]]:
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

    def prompt(self, new_message, add_system_to_prompt=False) -> dict:
        self.add_message("user", new_message)

        if not add_system_to_prompt:
            messages = self.get_messages_by_role("user")
        else:
            messages = self.messages

        response = openai.ChatCompletion.create(
            model=self.model, messages=messages, max_tokens=self.max_tokens
        )

        message = response.choices[0].message.to_dict()

        self.logger.debug(response)

        self.total_tokens_used += response.usage.total_tokens

        # self.api_history.append(response)
        self.messages.append(message)

        return response

    def __repr__(self) -> str:
        return f"<PromptContext model={self.model} messages={len(self.messages)}>"

    def __str__(self) -> str:
        return f"{self.get_used_tokens()=}\nMessaging with {self.model}:\n" + "\n".join(
            [
                f"{m['choices'][0]['message']['role']}: {m['choices'][0]['message']['content']}"
                for m in self.api_history
            ]
        )

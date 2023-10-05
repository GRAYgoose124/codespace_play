from typing import Self
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass

from .cmdli import CMDExit, CLI

from .prompt import PromptContext

Base = declarative_base()


@dataclass
class PromptsBin(Base):
    __tablename__ = "prompts_bin"

    id = Column(Integer, primary_key=True)
    prompt = Column(String)
    tags = Column(String)
    tokens_used = Column(Integer, default=0)


class ActiveSession(type):
    """This metaclass strips functions of the found ActiveCommands subclass and appends them to the ActiveSession parent class.

    It also applies the active_session_guard decorator to each function.
    """

    @staticmethod
    def active_session_guard(func, commit=True):
        def wrapper(self, *args, **kwargs):
            if self.active_session is None:
                # self.active_session = self.Session()
                raise Exception("No active session! Please use a context manager.")

            results = func(self, *args, **kwargs)

            if commit:
                self.active_session.commit()

            return results

        return wrapper

    def __new__(cls, name, bases, attrs):
        # add the active_session attribute to the class
        attrs["active_session"] = None

        # Get all methods of ActiveCommands subclass
        active_commands = attrs.pop("ActiveCommands")
        for attr_name, attr in active_commands.__dict__.items():
            if callable(attr) and not attr_name.startswith("__"):
                attrs[attr_name] = ActiveSession.active_session_guard(attr)

        # add the __enter__ and __exit__ methods
        attrs["__enter__"] = ActiveSession.__enter__
        attrs["__exit__"] = ActiveSession.__exit__

        return super().__new__(cls, name, bases, attrs)

    def __enter__(self):
        """You have to admit, it makes the delineation of Session access clearer."""
        self.active_session = self.Session()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.active_session.close()
        self.active_session = None


class PromptBinManager(metaclass=ActiveSession):
    def __init__(self, db_path: str):
        db_path = f"sqlite:///{db_path}/prompts_bin.db"
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    class ActiveCommands:
        def add_prompt(self, prompt: str, tags: str, tokens_used: int = 0):
            prompt_bin = PromptsBin(prompt=prompt, tags=tags, tokens_used=tokens_used)
            self.active_session.add(prompt_bin)
            self.active_session.commit()

        def get_prompts_by_tag(self, tag: str):
            prompts = (
                self.active_session.query(PromptsBin)
                .filter(PromptsBin.tags.contains(tag))
                .all()
            )
            return prompts

        def get_prompts_by_keyword(self, keyword: str):
            prompts = (
                self.active_session.query(PromptsBin)
                .filter(PromptsBin.prompt.contains(keyword))
                .all()
            )
            return prompts

        def get_all_prompts(self):
            prompts = self.active_session.query(PromptsBin).all()
            return prompts

        def delete_prompt(self, id: int):
            self.active_session.query(PromptsBin).filter(PromptsBin.id == id).delete()
            self.active_session.commit()

        def add_context(self, context: PromptContext):
            # add messages to bin and update db
            body = "\n".join(m for m in context.messages)
            self.add_prompt(
                body, f"{context.model},{context.title}", context.total_tokens_used
            )

    def interactive_loop(self):
        class BMCLI(CLI):
            @CLI.command
            def add():
                prompt = input("Enter a prompt to add to the bin:\n+ ")
                tags = input("Enter tags for the prompt:\n+ ")
                self.add_prompt(prompt, tags)

            @CLI.command
            def list():
                prompts = self.get_all_prompts()
                for i, p in enumerate(prompts):
                    print(f"{i}:\t{p.prompt}\t{p.tags}\t\tcost: {p.tokens_used}")

        BMCLI(command_prefix=None, prompt_str="# ").loop()

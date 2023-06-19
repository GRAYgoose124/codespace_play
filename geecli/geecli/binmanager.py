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


def active_session_guard(func):
    def wrapper(self, *args, **kwargs):
        if self.active_session is None:
            raise Exception("No active session! Please use a context manager.")

        return func(self, *args, **kwargs)

    return wrapper


class PromptBinManager:
    def __init__(self, db_path: str):
        db_path = f"sqlite:///{db_path}/prompts_bin.db"
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.active_session = None

    @active_session_guard
    def add_prompt(self, prompt: str, tags: str, tokens_used: int = 0):
        prompt_bin = PromptsBin(prompt=prompt, tags=tags, tokens_used=tokens_used)
        self.active_session.add(prompt_bin)
        self.active_session.commit()

    @active_session_guard
    def get_prompts_by_tag(self, tag: str):
        prompts = (
            self.active_session.query(PromptsBin)
            .filter(PromptsBin.tags.contains(tag))
            .all()
        )
        return prompts

    @active_session_guard
    def get_prompts_by_keyword(self, keyword: str):
        prompts = (
            self.active_session.query(PromptsBin)
            .filter(PromptsBin.prompt.contains(keyword))
            .all()
        )
        return prompts

    @active_session_guard
    def get_all_prompts(self):
        prompts = self.active_session.query(PromptsBin).all()
        return prompts

    @active_session_guard
    def delete_prompt(self, id: int):
        self.active_session.query(PromptsBin).filter(PromptsBin.id == id).delete()
        self.active_session.commit()

    @active_session_guard
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

            @CLI.command
            def exit():
                raise CMDExit

        BMCLI(command_prefix=None, prompt_str="# ").loop()

    def __enter__(self):
        """You have to admit, it makes the delineation of Session access clearer."""
        self.active_session = self.Session()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.active_session.close()
        self.active_session = None

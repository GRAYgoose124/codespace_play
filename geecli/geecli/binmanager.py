from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass

from geecli.geecli.prompt import PromptContext

Base = declarative_base()


@dataclass
class PromptsBin(Base):
    __tablename__ = "prompts_bin"

    id = Column(Integer, primary_key=True)
    prompt = Column(String)
    tags = Column(String)
    tokens_used = Column(Integer, default=0)


class PromptBinManager:
    def __init__(self, db_path="sqlite:///prompts_bin.db"):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_prompt(self, prompt: str, tags: str, tokens_used: int = 0):
        session = self.Session()
        prompt_bin = PromptsBin(prompt=prompt, tags=tags, tokens_used=tokens_used)
        session.add(prompt_bin)
        session.commit()
        session.close()

    def get_prompts_by_tag(self, tag: str):
        session = self.Session()
        prompts = session.query(PromptsBin).filter(PromptsBin.tags.contains(tag)).all()
        session.close()
        return prompts

    def get_prompts_by_keyword(self, keyword: str):
        session = self.Session()
        prompts = (
            session.query(PromptsBin).filter(PromptsBin.prompt.contains(keyword)).all()
        )
        session.close()
        return prompts

    def get_all_prompts(self):
        session = self.Session()
        prompts = session.query(PromptsBin).all()
        session.close()
        return prompts

    def delete_prompt(self, id: int):
        session = self.Session()
        session.query(PromptsBin).filter(PromptsBin.id == id).delete()
        session.commit()
        session.close()

    def add_context(self, context: PromptContext):
        # add messages to bin and update db
        body = "\n".join(m for m in context.messages)
        self.add_prompt(body, f"{context.model},", context.total_tokens_used)

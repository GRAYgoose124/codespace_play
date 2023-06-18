from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass

Base = declarative_base()


@dataclass
class PromptsBin(Base):
    __tablename__ = "prompts_bin"

    id = Column(Integer, primary_key=True)
    prompt = Column(String)
    tags = Column(String)


class PromptBinManager:
    def __init__(self, db_path="sqlite:///prompts_bin.db"):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_prompt(self, prompt: str, tags: str):
        session = self.Session()
        prompt_bin = PromptsBin(prompt=prompt, tags=tags)
        session.add(prompt_bin)
        session.commit()
        session.close()

    def get_prompts_by_tag(self, tag: str):
        session = self.Session()
        prompts = session.query(PromptsBin).filter(PromptsBin.tags.contains(tag)).all()
        session.close()
        return prompts

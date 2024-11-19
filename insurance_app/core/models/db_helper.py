from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from insurance_app.core.config import settings


class DatabaseHelper:
    def __init__(self, url: str, echo: bool = False) -> None:
        self.engine: Engine = create_engine(url=url, echo=echo)
        self.session_local: sessionmaker[Session] = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    def get_db(self) -> Session:
        db = self.session_local()
        try:
            yield db
        finally:
            db.close()


db_helper = DatabaseHelper(url=str(settings.DATABASE_URL))

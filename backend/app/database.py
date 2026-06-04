from sqlmodel import create_engine, Session
from .config import settings


engine = create_engine(settings.database_url, echo=True)

def get_session():
    """
    Dependency function to manage the database session lifecycle.
    It opens a session, yields it to the route, and closes it 
    automatically after the request is finished.
    """
    with Session(engine) as session:
        yield session
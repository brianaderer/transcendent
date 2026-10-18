"""The database address in the form SQLAlchemy and Alembic need."""


def sqlalchemy_url(database_url: str) -> str:
    """SQLAlchemy needs the driver named in the address; the rest of the code doesn't."""
    return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

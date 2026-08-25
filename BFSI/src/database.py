"""Database connection and engine management utilities."""
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import load_config


def get_engine(db_type: str = "sqlite", database: str = None) -> Engine:
    """Return a SQLAlchemy engine for the requested database type.

    Parameters
    ----------
    db_type : str
        "sqlite" (local dev) or "mysql" (target).
    database : str, optional
        MySQL schema name (e.g. "stgdb_ashwines"). When provided,
        the database name is appended to the connection URL so
        that to_sql() targets the correct schema.
    """
    db_cfg = load_config("database")[db_type]
    if db_type == "mysql":
        # URL-encode the password to handle special characters (e.g. "@")
        password = quote_plus(str(db_cfg["password"]))
        url = "{driver}://{user}:{password}@{host}:{port}".format(
            driver=db_cfg["driver"],
            user=db_cfg["user"],
            password=password,
            host=db_cfg["host"],
            port=db_cfg["port"],
        )
        if database:
            url += f"/{db_cfg["databases"][f'{database}']}"
    else:
        url = db_cfg["url"]
    return create_engine(url, future=True)


def init_database(engine: Engine) -> None:
    """Create all required schemas/tables if they do not exist.

    For SQLite this executes the DDL in ``ddl/bfsi_ddl_sqlite.sql``;
    for MySQL it runs ``ddl/bfsi_ddl.sql`` (which includes
    ``CREATE DATABASE`` statements).

    If the DDL file is not yet present, this is a no-op — tables
    will be auto-created by ``DataFrame.to_sql()`` at load time.
    """
    from .config import PROJECT_ROOT

    ddl_file = "bfsi_ddl_sqlite.sql" if "sqlite" in str(engine.url) else "bfsi_ddl.sql"
    ddl_path = PROJECT_ROOT / "ddl" / ddl_file

    if not ddl_path.exists():
        return  # to_sql will create tables automatically

    with open(ddl_path, "r", encoding="utf-8") as fh:
        ddl = fh.read()

    with engine.begin() as conn:
        for stmt in ddl.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))

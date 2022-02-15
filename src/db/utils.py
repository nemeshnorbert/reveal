import logging
import pathlib
import sqlite3

logger = logging.getLogger(__name__)


def is_database_exists(db_path):
    return pathlib.Path(db_path).exists()


def open_connection(db_path):
    if is_database_exists(db_path):
        logger.debug(f"Connecting to {db_path}")
        try:
            return sqlite3.connect(db_path)
        except Exception:
            logger.exception(f"Failed to connect to {db_path}")
            raise
    else:
        raise RuntimeError(f"Databse {db_path} doesn't exist")


def close_connection(connection):
    assert connection is not None
    logger.debug("Closing connection")
    connection.close()


def create_database(db_path):
    logger.info(f"Creating empty database at {db_path}")
    if not is_database_exists(db_path):
        try:
            connection = sqlite3.connect(db_path)
        except Exception:
            logging.exception("Failed to create database")
            raise
        else:
            close_connection(connection)
    else:
        raise RuntimeError(f"Database {db_path} already exists")


class DatabaseIO:
    def __init__(self, db_path):
        self._path = db_path
        self._connection = None

    def __enter__(self):
        self._connection = open_connection(self._path)
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        del exc_type
        del exc_val
        del exc_traceback
        close_connection(self._connection)
        self._connection = None
        return False

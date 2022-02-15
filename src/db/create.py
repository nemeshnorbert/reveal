import logging
import pathlib

import db.utils

logger = logging.getLogger(__name__)


def _create_tables(connection, script_path):
    with open(script_path, "r") as file_:
        logger.info(f"Creating tables via script at {script_path}")
        script = file_.read()
        connection.executescript(script)
        connection.commit()


def create_database(db_path, script_path=None):
    if script_path is None:
        script_path = pathlib.Path(__file__).parent / "create_db.sql"
    db.utils.create_database(db_path)
    with db.utils.open_connection(db_path) as connection:
        _create_tables(connection, script_path)

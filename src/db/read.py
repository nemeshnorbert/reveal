import logging

import db.utils

logger = logging.getLogger(__name__)


class _SqliteRatesReader(db.utils.DatabaseIO):
    def __init__(self, db_path):
        super().__init__(db_path)

    def read(self):
        command = self._get_read_command()
        logger.info(f"Reading data via command {command}")
        cursor = self._connection.cursor()
        yield from cursor.execute(command)
        self._connection.commit()

    @classmethod
    def _get_read_command(cls):
        return """SELECT date, symbol, rate FROM usd_rates;"""


class _SqliteRatesWriter(db.utils.DatabaseIO):
    def __init__(self, db_path):
        super().__init__(db_path)

    def write(self, values):
        command = self._get_write_command()
        logger.info(f"Writing data via command {command}")
        cursor = self._connection.cursor()
        cursor.executemany(command, values)
        self._connection.commit()

    @classmethod
    def _get_write_command(cls):
        return (
            "INSERT OR IGNORE INTO usd_rates(date, symbol, rate) "
            "VALUES (?, ?, ?);"
        )


def _build_rates_reader(db_path):
    return _SqliteRatesReader(db_path)


def _build_rates_writer(db_path):
    return _SqliteRatesWriter(db_path)


def _read_rates_impl(reader, writer):
    writer.write(reader.read())


def read_rates(db_path, src_db_path):
    logger.info(f"Writing conversion rates from {src_db_path} to {db_path}")
    with _build_rates_reader(src_db_path) as reader:
        with _build_rates_writer(db_path) as writer:
            _read_rates_impl(reader, writer)

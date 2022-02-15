import datetime
import json
import logging
import pathlib
import tempfile
import time

import db.utils
import db.read
import db.create

import rates.providers

logger = logging.getLogger(__name__)


class _ApiRatesReader:
    def __init__(self, providers):
        self._providers = providers
        self._has_access = [True] * len(self._providers)
        self._available_symbols = None

    def __enter__(self):
        self._available_symbols = self._collect_available_symbols()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        del exc_type
        del exc_val
        del exc_traceback
        return False

    def read(self, date, symbols):
        date = format(date)
        if symbols is None:
            symbols = self._available_symbols
        rates = {symbol: None for symbol in symbols}
        providers_count = len(self._providers)
        for provider_id in range(providers_count):
            provider = self._providers[provider_id]
            if not any(self._has_access):
                raise RuntimeError("Can't access any of the apis")
            if self._has_access[provider_id]:
                logger.debug(f"Using provider {provider}")
                bids = [
                    (date, symbol)
                    for symbol, rate in rates.items()
                    if rate is None
                ]
                provider_rates = provider.get_rates(bids)
                if provider_rates is not None:
                    for (_, symbol), rate in zip(bids, provider_rates):
                        rates[symbol] = rate
                else:
                    self._has_access[provider_id] = False
        return rates

    def _collect_available_symbols(self):
        symbols = set([])
        for provider in self._providers:
            symbols |= set(provider.get_symbols())
        return list(symbols)


class _SqliteRatesWriter(db.utils.DatabaseIO):
    def __init__(self, db_path):
        super().__init__(db_path)

    def write(self, date, rates):
        cursor = self._connection.cursor()
        values = (
            (date, symbol, rate)
            for symbol, rate in rates.items()
            if rate is not None
        )
        command = self._get_write_command()
        cursor.executemany(command, values)
        self._connection.commit()

    @classmethod
    def _get_write_command(cls):
        return (
            "INSERT OR IGNORE INTO usd_rates(date, symbol, rate) "
            "VALUES (?, ?, ?);"
        )


def _build_rates_reader(providers):
    return _ApiRatesReader(providers)


def _build_rates_writer(db_path):
    path = pathlib.Path(db_path)
    return _SqliteRatesWriter(path)


def _download_rates_date(reader, writer, date, symbols):
    report = {
        "error": False,
        "description": f"Successful download for date {date}",
    }
    logger.info(f"Downloading rates for date {date}")
    try:
        rates = reader.read(date, symbols)
        logger.info(f"Saving rates for {date}")
        writer.write(date, rates)
    except Exception:
        message = f"Failed to dowload rates for date {date}"
        logger.exception(message)
        report["error"] = True
        report["description"] = message
    return report


def _download_rates_batch(reader, writer, begin_date, end_date, symbols):
    logger.info(f"Dates from {begin_date} inclusive to {end_date} exclusive")
    symbols_list = ", ".join(symbols if symbols is not None else ["ALL"])
    logger.info(f"Symbols to be downloaded: {symbols_list}")

    reports = []
    date = begin_date
    while date < end_date:
        report = _download_rates_date(reader, writer, date, symbols)
        reports.append(report)
        date += datetime.timedelta(days=1)
    return reports


def _download_rates_impl(
    dbs_dir, apis, credentials, dates_ranges, symbols, read_delay, read_retries
):
    logger.info(f"Downloading data into {dbs_dir}")
    apis_list = ", ".join(apis)
    logger.info(f"Reading data from {apis_list}")

    providers = [
        rates.providers.build_api_provider(api, credentials[api], read_retries)
        for api in apis
    ]

    db_paths = []
    dbs_reports = []
    with _build_rates_reader(providers) as reader:
        for begin_date, end_date in dates_ranges:
            db_path = dbs_dir / f"rates_{begin_date}_{end_date}.db"
            db.create.create_database(db_path)
            with _build_rates_writer(db_path) as writer:
                db_report = _download_rates_batch(
                    reader=reader,
                    writer=writer,
                    begin_date=begin_date,
                    end_date=end_date,
                    symbols=symbols,
                )
                if read_delay > 0:
                    logger.info(f"Sleeping for {read_delay} seconds")
                    time.sleep(read_delay)
            db_paths.append(db_path)
            dbs_reports.append(db_report)
    return db_paths, dbs_reports


def _split_dates_in_ranges(begin_date, end_date, timespan):
    dates_ranges = []
    begin = begin_date
    while begin < end_date:
        end = min(begin + timespan, end_date)
        dates_ranges.append((begin, end))
        begin = end
    return dates_ranges


def _merge_dbs(db_path, src_dbs_paths):
    reports = []
    for src_db_path in src_dbs_paths:
        report = {
            "error": False,
            "description": f"Successfull merge from {src_db_path} to {db_path}",
        }
        try:
            db.read.read_rates(db_path, src_db_path)
        except Exception:
            message = f"Failed to merge {src_db_path} into {db_path}"
            logger.exception(message)
            report["error"] = True
            report["description"] = message
        reports.append(report)
    return reports


def _log_failed_downloads(download_reports):
    failures = [
        report
        for download_report in download_reports
        for report in download_report
        if report["error"]
    ]
    if logger.isEnabledFor(logging.INFO):
        failures_json = json.dumps(failures, indent=4, sort_keys=True)
        logger.info(f"Failed downloads:\n{failures_json}")


def _log_failed_merges(merge_reports):
    failures = [report for report in merge_reports if report["error"]]
    if logger.isEnabledFor(logging.INFO):
        failures_json = json.dumps(failures, indent=4, sort_keys=True)
        logger.info(f"Failed merges:\n{failures_json}")


def download_rates(
    db_path,
    apis,
    credentials,
    begin_date,
    end_date,
    symbols,
    batch_size,
    read_delay,
    read_retries,
):
    if not db.utils.is_database_exists(db_path):
        raise RuntimeError(f"Database {db_path} doesn't exist")

    if not (begin_date <= end_date):
        raise ValueError(
            f"begin_date={begin_date} must be less or equal"
            " to end_date={end_date}"
        )

    today = datetime.date.today()

    if not (end_date <= today):
        raise ValueError(
            f"end_date={end_date} must be not later than today={today}"
        )
    if not (read_delay >= 0):
        raise ValueError(
            f"read_delay={read_delay} must be non-negative integer"
        )
    if not (batch_size > 0):
        raise ValueError(f"batch_size={batch_size} must be a positive integer")
    if not (read_retries > 0):
        raise ValueError(
            f"read_retries={read_retries} must be a positive integer"
        )

    timespan = datetime.timedelta(days=batch_size)
    with tempfile.TemporaryDirectory() as temp_dir:
        dbs_dir = pathlib.Path(temp_dir)
        dates_ranges = _split_dates_in_ranges(begin_date, end_date, timespan)
        dbs_paths, download_reports = _download_rates_impl(
            dbs_dir=dbs_dir,
            apis=apis,
            credentials=credentials,
            symbols=symbols,
            dates_ranges=dates_ranges,
            read_delay=read_delay,
            read_retries=read_retries,
        )
        _log_failed_downloads(download_reports)

        merge_reports = _merge_dbs(db_path=db_path, src_dbs_paths=dbs_paths)
        _log_failed_merges(merge_reports)

#!/usr/bin/env python3

import argparse
import datetime
import logging
import logging.config
import os

import db.create
import db.delete
import db.download
import db.read
import db.setup


def _create_db(args):
    return db.create.create_database(args.path)


def _read_rates(args):
    return db.read.read_rates(args.path, args.src)


def _collect_app_ids_from_env(api):
    api_name = api.upper()
    variable_name = f"{api_name}_APP_IDS"
    if variable_name not in os.environ:
        raise RuntimeError(f"Environment variable {variable_name} is not set")
    return [
        dict(app_id=app_id) for app_id in os.environ[variable_name].split(":")
    ]


def _download_rates(args):
    credentials = {api: _collect_app_ids_from_env(api) for api in args.apis}

    fmt = "%Y-%m-%d"
    begin_date = datetime.datetime.strptime(args.begin_date, fmt).date()
    end_date = datetime.datetime.strptime(args.end_date, fmt).date()

    return db.download.download_rates(
        args.path,
        args.apis,
        credentials,
        begin_date,
        end_date,
        args.symbols,
        args.batch_size,
        args.read_delay,
        args.read_retries,
    )


def _delete_db(args):
    return db.delete.delete_database(args.path)


def _setup_db(args):
    return db.setup.setup_database(args.path, args.src)


def _parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Create, delete, download, and setup data in reveal app databse"
        )
    )
    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help="Log into file. Default is stdout",
    )
    subparsers = parser.add_subparsers(help="Subcommands")

    ############################################################################
    # create
    ############################################################################

    parser_create = subparsers.add_parser(
        "create", help="Create database with empty tables"
    )
    parser_create.add_argument(
        "path", type=str, help="Path to the new database"
    )
    parser_create.set_defaults(func=_create_db)

    ############################################################################
    # read
    ############################################################################

    parser_read_rates = subparsers.add_parser(
        "read_rates", help="Read usd rates data into the existing database"
    )
    parser_read_rates.add_argument(
        "path", type=str, help="Path to the database"
    )
    parser_read_rates.add_argument(
        "--src", type=str, required=True, help="Path to another sqlite database"
    )
    parser_read_rates.set_defaults(func=_read_rates)

    ############################################################################
    # download
    ############################################################################

    parser_download_rates = subparsers.add_parser(
        "download_rates", help="Download data from external api"
    )
    parser_download_rates.add_argument(
        "path", type=str, help="Path to the database"
    )
    parser_download_rates.add_argument(
        "--apis",
        type=str,
        nargs="+",
        choices=["openexchangerates", "currencylayer"],
        required=True,
        help="Name of the api",
    )
    parser_download_rates.add_argument(
        "--begin_date",
        type=str,
        default="1999-01-01",
        help="The first date to download rates for. Date format %Y-%m-%d",
    )
    parser_download_rates.add_argument(
        "--end_date",
        type=str,
        default="1999-01-01",
        help=(
            "The last date to download rates for. Date format %Y-%m-%d. "
            "This date is not included!"
        ),
    )
    parser_download_rates.add_argument(
        "--symbols",
        type=str,
        nargs="*",
        default=None,
        help=(
            "Currencies to download. "
            "If not specified then all available will be downloaded"
        ),
    )
    parser_download_rates.add_argument(
        "--batch_size",
        type=int,
        default=30,
        help="Number of days to be downloaded in one batch",
    )
    parser_download_rates.add_argument(
        "--read_delay",
        type=int,
        default=0,
        help="Delay (in seconds) between subsequent requests to providers",
    )
    parser_download_rates.add_argument(
        "--read_retries",
        type=int,
        default=3,
        help="Retries on on failed request",
    )
    parser_download_rates.set_defaults(func=_download_rates)

    ############################################################################
    # delete
    ############################################################################

    parser_delete = subparsers.add_parser("delete", help="Delete database")
    parser_delete.add_argument("path", type=str, help="Path to the database")
    parser_delete.set_defaults(func=_delete_db)

    ############################################################################
    # setup
    ############################################################################

    parser_setup = subparsers.add_parser(
        "setup", help="Setup ready to use database"
    )
    parser_setup.add_argument("path", type=str, help="Path to the database")
    parser_setup.add_argument(
        "--src", type=str, default=None, help="Database to read data from"
    )
    parser_setup.set_defaults(func=_setup_db)

    return parser.parse_args()


def _init_logging(log_file):
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {"level": "DEBUG", "handlers": ["console"]},
        "handlers": {
            "console": {
                "formatter": "console",
                "class": "logging.StreamHandler",
            },
        },
        "formatters": {
            "console": {
                "format": "[%(asctime)s][%(levelname)-9s] %(message)s",
            },
            "file": {
                "format": "[%(asctime)s][%(levelname)-9s] %(message)s",
            },
        },
    }
    if log_file is not None:
        log_config["root"]["handlers"].append("file")
        log_config["handlers"]["file"] = {
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": log_file,
        }
    logging.config.dictConfig(log_config)


def main():
    args = _parse_args()
    _init_logging(args.log_file)
    args.func(args)


if __name__ == "__main__":
    main()

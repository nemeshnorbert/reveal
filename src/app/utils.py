import json
import logging
import logging.config


def read_json(path):
    with open(path, "r") as file_:
        return json.load(file_)


def init_logging():
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
    logging.config.dictConfig(log_config)

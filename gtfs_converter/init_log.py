import logging
from logging import config


def config_worker_log():
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "basic": {
                    "format": "%(asctime)s [%(task_id)s] -- %(levelname)s -- %(message)s'"
                }
            },
            "filters": {"context": {"()": "pylogctx.AddContextFilter"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "filters": ["context"],
                    "formatter": "basic",
                }
            },
            "loggers": {
                "": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
                "urllib3": {"handlers": ["console"], "level": "WARNING",},
            },
        }
    )


def config_api_log():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s -- %(levelname)s -- %(message)s"
    )

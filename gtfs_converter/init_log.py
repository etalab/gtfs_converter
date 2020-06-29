import logging
from logging import config


def config():
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "basic": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s -- %(levelname)s [%(threadName)s] -- %(message)s'",
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
            "root": {"level": "DEBUG", "handlers": ["console"]},
        }
    )

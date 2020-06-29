import rq  # type: ignore
from redis import Redis
import os

import init_log
import logging


if __name__ == "__main__":
    init_log.config_worker_log()
    # Tell rq what Redis connection to use
    with rq.Connection(Redis.from_url(os.environ.get("REDIS_URL") or "redis://")):
        q = rq.Queue()
        rq.Worker(q).work()

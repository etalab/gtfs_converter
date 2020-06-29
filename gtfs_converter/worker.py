from rq import Connection, Queue, Worker  # type: ignore
from redis import Redis
import init_log
import logging


if __name__ == "__main__":
    init_log.config_worker_log()
    # Tell rq what Redis connection to use
    with Connection():
        q = Queue(connection=Redis())
        Worker(q).work()

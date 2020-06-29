from rq import Connection, Queue, Worker
from redis import Redis
import init_log

if __name__ == "__main__":
    init_log.config()
    # Tell rq what Redis connection to use
    with Connection():
        q = Queue(connection=Redis())
        Worker(q).work()

import os
import redis
from rq import Worker, Queue, Connection

redis_url = os.getenv('REDISTOGO_URL')
listen = ['high', 'default', 'low']

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
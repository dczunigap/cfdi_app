from __future__ import annotations

import os

from redis import Redis
from rq import Queue


def get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_queue(name: str = "default") -> Queue:
    redis = Redis.from_url(get_redis_url())
    return Queue(name, connection=redis)

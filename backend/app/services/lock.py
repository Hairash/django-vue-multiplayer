from contextlib import asynccontextmanager

from asgiref.sync import sync_to_async
from django.core.cache import cache


class LockException(Exception):
    pass


# Acquire the lock
async def acquire_redis_lock(lock_id, oid, timeout=1200):
    lock = f"lock:{lock_id}:{oid}"
    # Try to acquire the lock
    acquired = await sync_to_async(cache.add)(lock, 'true', timeout)
    if not acquired:
        raise LockException('You lost the race condition')
    return lock

# Release the lock
async def release_redis_lock(lock):
    await sync_to_async(cache.delete)(lock)


@asynccontextmanager
async def redis_lock(lock_id, oid):
    success = False
    lock = None
    try:
        lock = await acquire_redis_lock(lock_id, oid)
        success = True
        yield success, lock
    except LockException as e:
        yield success, lock
    finally:
        if lock:
            await release_redis_lock(lock)

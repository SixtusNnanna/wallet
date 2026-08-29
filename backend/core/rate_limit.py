from fastapi import HTTPException, status
from redis.asyncio import Redis
from backend.config import db_settings


_rate_limit_client = Redis.from_url(
    db_settings.get_redis_url(3),
    decode_responses=True,
    )

async def check_rate_limit(
        key: str,
        limit: int = 5,
        window: int = 60,
):
    redis_key = f"rate{key!s}"
    count = await _rate_limit_client.incr(redis_key)
    if count == 1:
        await _rate_limit_client.expire(key, window)

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many request, Try again in {window} seconds"
            )

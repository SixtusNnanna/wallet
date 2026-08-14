import redis.asyncio as redis
from backend.config import db_settings as settings


client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0, decode_responses=True
    )


async def blacklist_jti(jti: str) -> None:
    await client.set(jti, "blackedlisted")


async def is_jti_blacklisted(jti: str) -> bool:
    result = await client.get(jti)
    return result is not None

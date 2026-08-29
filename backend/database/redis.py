import enum
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
import redis.asyncio as redis
from backend.config import db_settings as settings
from functools import lru_cache


@lru_cache
def get_client() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0, decode_responses=True
        )


@lru_cache
def get_cache_client() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=1, decode_responses=True
    )

def get_redis_code_client() -> redis.Redis:
    return redis.Redis.from_url(
        settings.get_redis_url(7),
        decode_responses=True
        )



class CustomJsonEncorder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, enum.Enum):
            return str(obj)

        return super().default(obj)


async def blacklist_jti(jti: str) -> None:
    await get_client().set(jti, "blackedlisted")


async def is_jti_blacklisted(jti: str) -> bool:
    result = await get_client().get(jti)
    return result is not None


async def cache_data(cache_key: str, data, expire: int = 300):
    return await get_cache_client().set(
        cache_key,
        json.dumps(data,  cls=CustomJsonEncorder),
        ex=expire,
    )


async def get_cached_data(cache_key: str):
    data = await get_cache_client().get(cache_key)

    if data is None:
        return None

    return json.loads(data)


async def add_verification_code(user_id: str, code: str, ):
    code_key = f"password-reset:{code}"
    return await get_redis_code_client().set(code_key, user_id, ex=600)


async def get_verifcation_code(code: str):
    code_key = f"password-reset:{code}"
    return await get_redis_code_client().get(code_key)


async def delete_verification_code(code: str):
    code_key = f"password-reset:{code}"
    return await get_redis_code_client().delete(code_key)

import redis
import json
from typing import Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    """Wrapper para Redis con métodos helper"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        """Verifica conectividad con Redis"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    def publish(self, channel: str, message: dict) -> None:
        """Publica un mensaje en un canal"""
        try:
            self.client.publish(channel, json.dumps(message))
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Redis publish failed: {e}")
    
    def subscribe(self, channel: str):
        """Retorna un PubSub object suscrito al canal"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    def push_to_queue(self, queue: str, data: dict) -> None:
        """Agrega un item a una cola (lista)"""
        try:
            self.client.lpush(queue, json.dumps(data))
            logger.debug(f"Pushed to queue {queue}: {data}")
        except Exception as e:
            logger.error(f"Redis lpush failed: {e}")
    
    def pop_from_queue(self, queue: str, timeout: int = 0) -> Optional[dict]:
        """Saca un item de una cola (bloqueante)"""
        try:
            result = self.client.brpop(queue, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        except Exception as e:
            logger.error(f"Redis brpop failed: {e}")
            return None

redis_client = RedisClient()

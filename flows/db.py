"""MongoDB 连接：复用项目已有的 pymongo 依赖，提供单例 client。"""
import logging
from pymongo import MongoClient

from flows.config import MONGO_URI

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_db():
    """返回 stock 数据库句柄（单例连接）。"""
    global _client
    if _client is None:
        if not MONGO_URI:
            raise RuntimeError("缺少 MongoDB 连接串：请在 .env 中配置 DIRECT_URL")
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=20000,
            maxPoolSize=10,
        )
        logger.info("MongoDB 连接已建立")
    return _client["stock"]

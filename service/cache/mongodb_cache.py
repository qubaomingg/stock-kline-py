#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB缓存服务
用于缓存股票市场列表查询结果，缓存有效期2天
优化版本：添加内存LRU缓存层，大幅提升读取性能
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from functools import lru_cache
from collections import OrderedDict
import json
from bson import json_util
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# 设置日志
logger = logging.getLogger(__name__)


class MemoryLRUCache:
    """内存LRU缓存，用于快速访问热点数据"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        初始化内存LRU缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存有效期（秒）
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """从内存缓存获取数据"""
        if key not in self.cache:
            return None
        
        # 检查是否过期
        if time.time() - self.timestamps.get(key, 0) > self.ttl_seconds:
            self.delete(key)
            return None
        
        # 移动到末尾表示最近使用
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """设置内存缓存"""
        # 如果已存在，先删除
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            # 如果超过最大大小，删除最旧的
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self.delete(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """删除内存缓存"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self) -> None:
        """清空内存缓存"""
        self.cache.clear()
        self.timestamps.clear()


class MongoDBCache:
    """MongoDB缓存管理器 - 优化版本，包含内存缓存层和延迟连接"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化MongoDB缓存

        Args:
            connection_string: MongoDB连接字符串，如果为None则从环境变量读取
        """
        self.connection_string = connection_string or os.environ.get(
            "MONGODB_URL"
        ) or os.environ.get("DIRECT_URL")
        self.client = None
        self.db = None
        self.collection = None

        # 初始化内存缓存 - 市场数据比较大，设置合理的TTL
        self.memory_cache = MemoryLRUCache(max_size=20, ttl_seconds=1800)  # 30分钟

        # 标记：是否已尝试连接（用于延迟连接）
        self._connection_attempted = False
        self._connect_error = None

        # 注意：不在构造函数中立即连接！
        # 连接推迟到首次实际使用时进行

    def _ensure_connected(self):
        """确保MongoDB已连接（延迟连接）- 首次使用时才建立连接"""
        if self._connection_attempted:
            # 已经尝试过连接，无论成功失败都不再尝试
            return

        self._connection_attempted = True

        if not self.connection_string:
            logger.warning("MongoDB连接字符串未设置，仅使用内存缓存")
            return

        try:
            logger.info(f"正在延迟连接MongoDB...")
            start_time = time.time()
            self._connect()
            connect_time = time.time() - start_time
            logger.info(f"MongoDB延迟连接完成，耗时 {connect_time:.2f}s")
        except Exception as e:
            self._connect_error = e
            logger.warning(f"MongoDB延迟连接失败，仅使用内存缓存: {type(e).__name__}")

    def _connect(self):
        """连接到MongoDB数据库 - 优化版本：更好的超时处理"""
        if not self.connection_string:
            logger.warning("MongoDB连接字符串未设置，仅使用内存缓存")
            return

        try:
            logger.info(f"正在连接MongoDB...")
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,   # 服务器选择超时5秒（更短）
                connectTimeoutMS=5000,            # 连接超时5秒
                socketTimeoutMS=10000,            # socket超时10秒
                maxPoolSize=10,                   # 减小连接池大小
                minPoolSize=0,                    # 最小连接数0
                maxIdleTimeMS=30000,              # 空闲连接30秒后关闭
                waitQueueTimeoutMS=5000,          # 等待队列超时5秒
                heartbeatFrequencyMS=10000,        # 心跳频率10秒
                retryWrites=False,                 # 禁用写入重试
                retryReads=False                   # 禁用读取重试
            )
            # 测试连接 - 快速失败
            self.client.admin.command('ping', maxTimeMS=2000)
            self.db = self.client.get_database("stock")
            self.collection = self.db.get_collection("MarketStockCache")

            # 创建索引：缓存键和过期时间
            # 在后台创建索引以防阻塞查询，设置超时保护
            logger.debug("正在验证缓存索引...")
            try:
                self.collection.create_index([("cache_key", ASCENDING)], unique=True, background=True)
                self.collection.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, background=True)
            except Exception as idx_e:
                logger.debug(f"索引验证: {idx_e}")

            logger.info("MongoDB连接成功")

        except (ConnectionFailure, ServerSelectionTimeoutError, TimeoutError) as e:
            logger.warning(f"MongoDB连接失败，仅使用内存缓存: {type(e).__name__}")
            self.client = None
            self.db = None
            self.collection = None
        except Exception as e:
            logger.warning(f"MongoDB连接异常，仅使用内存缓存: {type(e).__name__}")
            self.client = None
            self.db = None
            self.collection = None

    def is_connected(self) -> bool:
        """检查是否连接到MongoDB"""
        return self.client is not None and self.collection is not None

    def _generate_cache_key(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        生成缓存键

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)

        Returns:
            缓存键字符串
        """
        # 标准化参数
        code_lower = code.lower()
        start_str = start_date or ""
        end_str = end_date or ""

        # 生成缓存键：格式为 {type}:{code}:{start_date}:{end_date}
        # 单参数调用（市场股票数据）：market:{code}
        # 三参数调用（K线数据）：kline:{code}:{start_date}:{end_date}
        if start_str == "" and end_str == "":
            return f"market:{code_lower}"
        else:
            return f"kline:{code_lower}:{start_str}:{end_str}"

    def get(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        从缓存获取数据 - 优化版本：优先从内存缓存读取，延迟连接MongoDB

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)

        Returns:
            缓存数据或None
        """
        cache_key = self._generate_cache_key(code, start_date, end_date)

        # 第一步：优先从内存缓存获取（微秒级响应）
        memory_data = self.memory_cache.get(cache_key)
        if memory_data is not None:
            return memory_data

        # 确保MongoDB已连接（延迟连接）
        self._ensure_connected()

        # 内存缓存未命中，检查MongoDB连接
        if not self.is_connected():
            return None

        try:
            from datetime import datetime
            now = datetime.utcnow()

            # 添加查询超时，优化查询 - 只返回需要的字段
            cache_item = self.collection.find_one(
                {
                    'cache_key': cache_key,
                    'expires_at': {'$gt': now}
                },
                projection={'data': 1, '_id': 0},  # 只返回data字段，减少数据传输
                max_time_ms=2000  # 查询超时2秒（更短）
            )

            if cache_item and cache_item.get("data"):
                logger.info(f"MongoDB缓存命中: {cache_key}")
                
                # 同步到内存缓存，加速下次访问
                data = cache_item["data"]
                self.memory_cache.set(cache_key, data)
                
                return data
            else:
                return None

        except Exception as e:
            logger.debug(f"MongoDB查询失败: {type(e).__name__}")
            return None

    def set(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, data: Dict[str, Any] = None, ttl_days: int = 2) -> bool:
        """
        设置K线数据缓存 - 优化版本：同时写入内存缓存，延迟连接MongoDB

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            data: 要缓存的数据
            ttl_days: 缓存有效期（天数），默认2天

        Returns:
            是否成功
        """
        # 检查数据是否为空，如果为空则不进行缓存
        if not data:
            return False

        # 检查如果是字典且包含data字段，data字段是否为空数组
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list) and len(data['data']) == 0:
            return False

        # 检查如果是字典且包含stocks字段，stocks字段是否为空数组
        if isinstance(data, dict) and 'stocks' in data and isinstance(data['stocks'], list) and len(data['stocks']) == 0:
            return False

        # 统一使用_generate_cache_key生成缓存键
        cache_key = self._generate_cache_key(code, start_date, end_date)

        # 第一步：优先写入内存缓存（微秒级）
        self.memory_cache.set(cache_key, data)

        # 确保MongoDB已连接（延迟连接）
        self._ensure_connected()

        # 如果MongoDB未连接，只使用内存缓存
        if not self.is_connected():
            return True

        expires_at = datetime.utcnow() + timedelta(days=ttl_days)

        try:
            # 使用upsert操作，如果存在则更新，不存在则插入
            result = self.collection.update_one(
                {"cache_key": cache_key},
                {
                    "$set": {
                        "cache_key": cache_key,
                        "code": code.lower(),
                        "start_date": start_date,
                        "end_date": end_date,
                        "data": data,
                        "expires_at": expires_at,
                        "cached_at": datetime.utcnow(),
                        "ttl_days": ttl_days
                    }
                },
                upsert=True
            )

            logger.info(f"MongoDB缓存已写入: {cache_key}")
            return result.acknowledged

        except Exception as e:
            logger.debug(f"MongoDB写入失败: {type(e).__name__}")
            # MongoDB失败没关系，内存缓存已经可以用了
            return True

    def delete(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
        """
        删除K线数据缓存 - 优化版本：同时删除内存缓存

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)

        Returns:
            是否成功
        """
        # 统一使用_generate_cache_key生成缓存键
        cache_key = self._generate_cache_key(code, start_date, end_date)
        
        # 第一步：删除内存缓存
        self.memory_cache.delete(cache_key)

        if not self.is_connected():
            return True

        try:
            self.collection.delete_one({"cache_key": cache_key})
            return True

        except Exception as e:
            logger.debug(f"MongoDB删除失败: {type(e).__name__}")
            # 内存缓存已经删除，返回成功
            return True

    def clear_all(self) -> bool:
        """清除所有缓存 - 优化版本：同时清空内存缓存"""
        # 第一步：清空内存缓存
        self.memory_cache.clear()
        
        if not self.is_connected():
            return True

        try:
            self.collection.delete_many({})
            return True

        except Exception as e:
            logger.debug(f"MongoDB清空失败: {type(e).__name__}")
            # 内存缓存已清空，返回成功
            return True

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.is_connected():
            return {"connected": False}

        try:
            total = self.collection.count_documents({})
            now = datetime.utcnow()
            valid = self.collection.count_documents({"expires_at": {"$gt": now}})
            expired = total - valid

            return {
                "connected": True,
                "total_cache_items": total,
                "valid_cache_items": valid,
                "expired_cache_items": expired,
                "database": self.db.name,
                "collection": self.collection.name
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return {"connected": False, "error": str(e)}

    def close(self):
        """关闭数据库连接"""
        if self.client:
            logger.info("关闭MongoDB连接")
            self.client.close()


# 全局缓存实例
_cache_instance = None


def get_cache() -> MongoDBCache:
    """
    获取全局缓存实例（单例模式）

    Returns:
        MongoDBCache实例
    """
    global _cache_instance
    if _cache_instance is None:
        try:
            # 尝试导入pymongo，如果不可用则使用模拟缓存
            import pymongo
            _cache_instance = MongoDBCache()
        except ImportError:
            # 如果没有pymongo，创建一个模拟缓存对象
            logger.warning("pymongo不可用，使用模拟缓存（无实际缓存功能）")
            class MockCache:
                def __init__(self):
                    self.cache = {}
                def get(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
                    return None
                def set(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, data: Dict[str, Any] = None, ttl_days: int = 2) -> bool:
                    return True
                def delete(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
                    return True
                def is_connected(self):
                    return False
                def close(self):
                    pass
            _cache_instance = MockCache()
    return _cache_instance


def cache_market_stocks(market_code: str, data: Dict[str, Any]) -> bool:
    """
    缓存市场股票列表（便捷函数）

    Args:
        market_code: 市场代码
        data: 股票列表数据

    Returns:
        是否成功
    """
    cache = get_cache()
    return cache.set(market_code, data)


def get_cached_market_stocks(market_code: str) -> Optional[Dict[str, Any]]:
    """
    获取缓存的市場股票列表（便捷函数）

    Args:
        market_code: 市场代码

    Returns:
        缓存数据或None
    """
    cache = get_cache()
    return cache.get(market_code)


def cache_kline_data(code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, data: Dict[str, Any] = None) -> bool:
    """
    缓存K线数据（便捷函数）

    Args:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD格式)
        end_date: 结束日期 (YYYY-MM-DD格式)
        data: K线数据

    Returns:
        是否成功
    """
    cache = get_cache()
    return cache.set(code, start_date, end_date, data)


def get_cached_kline_data(code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    获取缓存的K线数据（便捷函数）

    Args:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD格式)
        end_date: 结束日期 (YYYY-MM-DD格式)

    Returns:
        缓存数据或None
    """
    cache = get_cache()
    return cache.get(code, start_date, end_date)


def delete_cached_kline_data(code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
    """
    删除缓存的K线数据（便捷函数）

    Args:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD格式)
        end_date: 结束日期 (YYYY-MM-DD格式)

    Returns:
        是否成功
    """
    cache = get_cache()
    return cache.delete(code, start_date, end_date)

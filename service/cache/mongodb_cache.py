#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB缓存服务
用于缓存股票市场列表查询结果，缓存有效期2天
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
import json
from bson import json_util

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# 设置日志
logger = logging.getLogger(__name__)


class MongoDBCache:
    """MongoDB缓存管理器"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化MongoDB缓存
        
        Args:
            connection_string: MongoDB连接字符串，如果为None则从环境变量读取
        """
        self.connection_string = connection_string or os.environ.get(
            "MONGODB_URL"
        )
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """连接到MongoDB数据库"""
        try:
            logger.info(f"正在连接MongoDB: {self.connection_string[:50]}...")
            self.client = MongoClient(
                self.connection_string, 
                serverSelectionTimeoutMS=10000,  # 增加到10秒
                connectTimeoutMS=10000,          # 连接超时10秒
                socketTimeoutMS=30000,           # socket超时30秒
                maxPoolSize=50,                  # 连接池大小
                minPoolSize=10                   # 最小连接数
            )
            # 测试连接
            self.client.admin.command('ping')
            self.db = self.client.get_database("stock")
            self.collection = self.db.get_collection("MarketStockCache")
            
            # 创建索引：缓存键和过期时间
            logger.info("正在创建缓存索引...")
            self.collection.create_index([("cache_key", ASCENDING)], unique=True)
            self.collection.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
            
            logger.info(f"成功连接到MongoDB数据库: {self.db.name}, 集合: {self.collection.name}")
            logger.debug(f"连接字符串: {self.connection_string}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"连接MongoDB失败: {e}")
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
        从缓存获取数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            
        Returns:
            缓存数据或None
        """
        if not self.is_connected():
            logger.warning("MongoDB未连接，无法获取缓存")
            return None
        
        try:
            cache_key = self._generate_cache_key(code, start_date, end_date)
            logger.info(f"尝试从缓存获取 {code.upper()} 数据")
            logger.debug(f"缓存键: {cache_key}")
            
            from datetime import datetime
            now = datetime.utcnow()
            
            # 添加查询超时
            query_start = time.time()
            cache_item = self.collection.find_one(
                {
                    'cache_key': cache_key,
                    'expires_at': {'$gt': now}
                },
                max_time_ms=5000  # 查询超时5秒
            )
            query_end = time.time()
            logger.debug(f"MongoDB查询耗时: {query_end - query_start:.3f}秒")
            
            if cache_item:
                logger.info(f"从缓存获取 {code.upper()} 数据")
                logger.debug(f"缓存键: {cache_key}, 过期时间: {cache_item.get('expires_at')}")
                # 优化：直接返回BSON数据，避免JSON转换开销
                return cache_item["data"]
            else:
                logger.info(f"缓存未找到或已过期: {code.upper()}")
                logger.debug(f"缓存键: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"获取缓存失败: {e}", exc_info=True)
            return None
    
    def set(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, data: Dict[str, Any] = None, ttl_days: int = 2) -> bool:
        """
        设置K线数据缓存
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            data: 要缓存的数据
            ttl_days: 缓存有效期（天数），默认2天
            
        Returns:
            是否成功
        """
        if not self.is_connected():
            return False
        
        # 统一使用_generate_cache_key生成缓存键
        cache_key = self._generate_cache_key(code, start_date, end_date)
        
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
            
            logger.info(f"缓存 {code.upper()} 数据，有效期 {ttl_days} 天")
            logger.debug(f"缓存键: {cache_key}, 过期时间: {expires_at}")
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}", exc_info=True)
            return False
    
    def delete(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
        """
        删除K线数据缓存
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            
        Returns:
            是否成功
        """
        if not self.is_connected():
            return False
        
        # 统一使用_generate_cache_key生成缓存键
        cache_key = self._generate_cache_key(code, start_date, end_date)
        
        try:
            logger.info(f"删除 {code.upper()} K线数据缓存")
            result = self.collection.delete_one({"cache_key": cache_key})
            if result.deleted_count > 0:
                logger.info(f"成功删除 {code.upper()} K线数据缓存")
            else:
                logger.info(f"{code.upper()} K线数据缓存不存在")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"删除缓存失败: {e}", exc_info=True)
            return False
    
    def clear_all(self) -> bool:
        """清除所有缓存"""
        if not self.is_connected():
            return False
        
        try:
            logger.info("清除所有缓存")
            result = self.collection.delete_many({})
            logger.info(f"清除所有缓存，删除 {result.deleted_count} 条记录")
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"清除缓存失败: {e}", exc_info=True)
            return False
    
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
        _cache_instance = MongoDBCache()
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
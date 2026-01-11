#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存装饰器
用于为函数添加MongoDB缓存功能
"""

import functools
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from .mongodb_cache import get_cache

# 设置日志
logger = logging.getLogger(__name__)


def cache_market_stocks(market_code_param: str = "market"):
    """
    缓存股票市场列表的装饰器

    Args:
        market_code_param: 函数参数中市场代码的参数名，默认为'market'

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Dict[str, Any]]:
            # 获取市场代码
            market_code = None

            # 从关键字参数中获取
            if market_code_param in kwargs:
                market_code = kwargs[market_code_param]
            # 从位置参数中获取（如果函数有market参数）
            elif args:
                # 尝试从函数签名获取参数位置
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())

                if market_code_param in params:
                    param_index = params.index(market_code_param)
                    if param_index < len(args):
                        market_code = args[param_index]

            if not market_code:
                # 如果没有明确的市场代码，尝试从函数名推断
                func_name = func.__name__.lower()
                if 'cn' in func_name:
                    market_code = 'cn'
                elif 'hk' in func_name:
                    market_code = 'hk'
                elif 'us' in func_name:
                    market_code = 'us'
                else:
                    market_code = 'unknown'

            # 尝试从缓存获取
            logger.info(f"尝试从缓存获取 {market_code.upper()} 市场股票列表")
            logger.debug(f"函数: {func.__name__}, 市场代码参数: {market_code_param}")

            cache = get_cache()
            cached_data = cache.get(market_code)

            if cached_data:
                # 添加缓存标记
                cached_data["_cached"] = True
                cached_data["_cache_timestamp"] = datetime.utcnow().isoformat()
                logger.info(f"缓存命中: {market_code.upper()} 市场，返回缓存数据")
                logger.debug(f"缓存数据大小: {len(str(cached_data))} 字符")
                return cached_data

            # 缓存未命中，调用原函数
            logger.info(f"缓存未命中: {market_code.upper()} 市场，调用原函数")
            result = func(*args, **kwargs)

            if result:
                # 添加缓存标记
                result["_cached"] = False
                result["_cache_timestamp"] = datetime.utcnow().isoformat()

                # 缓存结果
                logger.info(f"正在缓存 {market_code.upper()} 市场数据")
                cache_success = cache.set(market_code, data=result, ttl_days=3)

                if cache_success:
                    logger.info(f"成功缓存 {market_code.upper()} 市场数据")
                    logger.debug(f"缓存数据大小: {len(str(result))} 字符")
                else:
                    logger.warning(f"缓存 {market_code.upper()} 市场数据失败")
            else:
                logger.warning(f"原函数返回空结果，跳过缓存: {market_code.upper()} 市场")

            return result

        return wrapper

    return decorator


def cache_by_key(cache_key_func: Callable):
    """
    通用缓存装饰器，根据自定义函数生成缓存键

    Args:
        cache_key_func: 生成缓存键的函数，接收原函数的参数，返回缓存键字符串

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_key_func(*args, **kwargs)

            # 尝试从缓存获取
            logger.info(f"尝试从缓存获取键: '{cache_key}'")
            logger.debug(f"函数: {func.__name__}")

            cache = get_cache()
            cached_data = cache.get(cache_key)

            if cached_data:
                cached_data["_cached"] = True
                cached_data["_cache_timestamp"] = datetime.utcnow().isoformat()
                logger.info(f"缓存命中: 键 '{cache_key}'，返回缓存数据")
                logger.debug(f"缓存数据大小: {len(str(cached_data))} 字符")
                return cached_data

            # 缓存未命中，调用原函数
            logger.info(f"缓存未命中: 键 '{cache_key}'，调用原函数")
            result = func(*args, **kwargs)

            if result:
                result["_cached"] = False
                result["_cache_timestamp"] = datetime.utcnow().isoformat()

                # 使用cache_key作为market_code参数缓存
                logger.info(f"正在缓存键: '{cache_key}' 的数据")
                cache_success = cache.set(cache_key, result)

                if cache_success:
                    logger.info(f"成功缓存键: '{cache_key}' 的数据")
                    logger.debug(f"缓存数据大小: {len(str(result))} 字符")
                else:
                    logger.warning(f"缓存键: '{cache_key}' 的数据失败")
            else:
                logger.warning(f"原函数返回空结果，跳过缓存: 键 '{cache_key}'")

            return result

        return wrapper

    return decorator


@cache_by_key(lambda market_code: f"market:{market_code}")
def get_market_stocks(market_code: str) -> Dict[str, Any]:
    """
    获取指定市场的股票列表

    Args:
        market_code: 市场代码 (hk, us, cn)

    Returns:
        股票列表数据
    """
    # 这里应该调用实际的API获取股票列表
    # 为了演示，返回空数据
    return {"market": market_code, "stocks": []}


def cache_kline_data():
    """
    缓存K线数据的装饰器

    这个装饰器会缓存K线数据，缓存键由股票代码、开始日期和结束日期组成
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数参数信息
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())

            # 从参数中提取股票代码、开始日期和结束日期
            code = None
            start_date = None
            end_date = None

            # 首先检查关键字参数
            if 'code' in kwargs:
                code = kwargs['code']
            if 'start_date' in kwargs:
                start_date = kwargs['start_date']
            if 'end_date' in kwargs:
                end_date = kwargs['end_date']

            # 如果没有在关键字参数中找到，检查位置参数
            if not code and 'code' in params:
                param_index = params.index('code')
                if param_index < len(args):
                    code = args[param_index]

            if not start_date and 'start_date' in params:
                param_index = params.index('start_date')
                if param_index < len(args):
                    start_date = args[param_index]

            if not end_date and 'end_date' in params:
                param_index = params.index('end_date')
                if param_index < len(args):
                    end_date = args[param_index]

            if not code:
                # 如果没有股票代码，直接调用原函数
                logger.warning("无法获取股票代码，跳过缓存")
                return func(*args, **kwargs)

            # 尝试从缓存获取
            logger.info(f"尝试从缓存获取 {code.upper()} K线数据，开始日期: {start_date}, 结束日期: {end_date}")
            logger.debug(f"函数: {func.__name__}")

            cache = get_cache()
            cached_data = cache.get(code, start_date, end_date)

            if cached_data:
                # 添加缓存标记
                cached_data["_cached"] = True
                cached_data["_cache_timestamp"] = datetime.utcnow().isoformat()
                logger.info(f"缓存命中: {code.upper()} K线数据，返回缓存数据")
                logger.debug(f"缓存数据大小: {len(str(cached_data))} 字符")
                return cached_data

            # 缓存未命中，调用原函数
            logger.info(f"缓存未命中: {code.upper()} K线数据，调用原函数")
            result = func(*args, **kwargs)

            if result:
                # 添加缓存标记
                result["_cached"] = False
                result["_cache_timestamp"] = datetime.utcnow().isoformat()

                # 缓存结果
                logger.info(f"正在缓存 {code.upper()} K线数据")
                cache_success = cache.set(code, start_date, end_date, result, ttl_days=1)

                if cache_success:
                    logger.info(f"成功缓存 {code.upper()} K线数据")
                    logger.debug(f"缓存数据大小: {len(str(result))} 字符")
                else:
                    logger.warning(f"缓存 {code.upper()} K线数据失败")
            else:
                logger.warning(f"原函数返回空结果，跳过缓存: {code.upper()} K线数据")

            return result

        return wrapper

    return decorator

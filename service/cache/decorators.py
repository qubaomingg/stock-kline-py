#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存装饰器
用于为函数添加MongoDB缓存功能
"""

import functools
import logging
import time
import re
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from .mongodb_cache import get_cache

# 设置日志
logger = logging.getLogger(__name__)


def _infer_market_from_code(code: str) -> str:
    """从股票代码推断市场类型

    Args:
        code: 股票代码

    Returns:
        市场类型: 'a' (A股), 'hk' (港股), 'us' (美股), 'unknown'
    """
    if not code:
        return "unknown"

    clean_code = code.strip().upper()

    # 纯数字 6 位 → A股（主板/创业板/科创板）
    if re.match(r'^\d{6}$', clean_code):
        # A股: 600/601/603 沪市主板, 000/001 深市主板,
        # 002/003 中小板, 300 创业板, 688 科创板, 4/8 北交所
        if clean_code.startswith(('600', '601', '603', '605',
                                   '000', '001',
                                   '002', '003',
                                   '300', '301',
                                   '688', '689')):
            return "a"
        return "a"  # 默认 6 位数字按 A股 处理

    # 纯数字 4 或 5 位 → 港股
    if re.match(r'^\d{4,5}$', clean_code):
        return "hk"

    # 含字母，非纯数字 → 美股
    if re.match(r'^[A-Z]', clean_code) or re.match(r'.*[A-Z].*', clean_code):
        return "us"

    return "unknown"



def cache_market_stocks(market_code_param: str = "market"):
    """
    缓存股票市场列表的装饰器

    Args:
        market_code_param: 函数参数中市场代码的参数名，默认为'market'
        force: 从 kwargs 中读取，force=True 时跳过缓存查询

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Dict[str, Any]]:
            # 获取市场代码
            market_code = None
            # 获取 force 参数
            force = kwargs.pop('force', False) or kwargs.pop('force_refresh', False)

            # 从关键字参数中获取
            if market_code_param in kwargs:
                market_code = kwargs[market_code_param]
            # 从位置参数中获取（如果函数有market参数）
            elif args:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())

                if market_code_param in params:
                    param_index = params.index(market_code_param)
                    if param_index < len(args):
                        market_code = args[param_index]

            if not market_code:
                func_name = func.__name__.lower()
                if 'a' in func_name:
                    market_code = 'a'
                elif 'hk' in func_name:
                    market_code = 'hk'
                elif 'us' in func_name:
                    market_code = 'us'
                else:
                    market_code = 'unknown'

            # 初始化缓存
            cache = get_cache()

            # force=True 时跳过缓存查询
            if not force:
                cached_data = cache.get(market_code)
                if cached_data:
                    cached_data["_cached"] = True
                    cached_data["_cache_timestamp"] = datetime.utcnow().isoformat()
                    logger.info(f"[{market_code.upper()}] 缓存命中，共 {cached_data.get('count', 0)} 只股票")
                    return cached_data

            # 缓存未命中或 force=True，调用原函数
            log_prefix = f"[{market_code.upper()}]"
            if force:
                logger.info(f"{log_prefix} force=true，跳过缓存，直接获取数据...")
            else:
                logger.info(f"{log_prefix} 缓存未命中，正在获取数据...")

            result = func(*args, **kwargs)

            if result:
                result["_cached"] = False
                result["_cache_timestamp"] = datetime.utcnow().isoformat()

                # 写入缓存
                cache_success = cache.set(market_code, data=result, ttl_days=5)

                if cache_success:
                    logger.info(f"{log_prefix} 成功写入缓存，共 {result.get('count', 0)} 只股票")
                else:
                    logger.warning(f"{log_prefix} 缓存写入失败")
            else:
                logger.warning(f"{log_prefix} 原函数返回空结果，跳过缓存")

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
        market_code: 市场代码 (hk, us, a)

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

            # 从参数中提取股票代码、开始日期、结束日期
            # force: True 表示强制跳过缓存，直接从数据源获取
            code = None
            start_date = None
            end_date = None
            force = False

            # 首先检查关键字参数
            if 'code' in kwargs:
                code = kwargs['code']
            if 'start_date' in kwargs:
                start_date = kwargs['start_date']
            if 'end_date' in kwargs:
                end_date = kwargs['end_date']
            if 'force' in kwargs:
                force = bool(kwargs['force'])

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

            if not force and 'force' in params:
                param_index = params.index('force')
                if param_index < len(args):
                    force = bool(args[param_index])

            if not code:
                # 如果没有股票代码，直接调用原函数
                logger.warning("无法获取股票代码，跳过缓存")
                return func(*args, **kwargs)

            # 从代码推断市场类型（用于日志展示）
            market_type = _infer_market_from_code(code)
            log_prefix = f"[{func.__name__}] [market={market_type}] {code.upper()}"

            # 初始化 cache 实例（force=True 和正常路径都可能需要写缓存）
            cache = get_cache()

            # 如果 force=True，直接跳过缓存查询
            if force:
                logger.info(f"{log_prefix} 🔄 强制刷新模式，跳过缓存，直接从数据源获取...")
                t_start = time.time()
                try:
                    # 将 force 从 kwargs 中移除，避免传给底层函数（可能不支持此参数）
                    func_kwargs = {k: v for k, v in kwargs.items() if k != 'force'}
                    result = func(*args, **func_kwargs)
                except Exception as e:
                    elapsed = time.time() - t_start
                    logger.error(f"{log_prefix} ❌ 原函数调用异常 ({elapsed:.1f}s): {e}")
                    raise
                elapsed = time.time() - t_start
            else:
                # 正常流程：先尝试从缓存获取
                logger.info(f"{log_prefix} 尝试从缓存获取K线数据 (日期: {start_date or 'auto'} ~ {end_date or 'auto'})")

                t0 = time.time()
                cached_data = cache.get(code, start_date, end_date)
                cache_lookup_ms = int((time.time() - t0) * 1000)

                if cached_data:
                    # 添加缓存标记
                    cached_data["_cached"] = True
                    cached_data["_cache_timestamp"] = datetime.utcnow().isoformat()
                    data_size = len(str(cached_data))
                    logger.info(f"{log_prefix} ✅ 缓存命中 ({cache_lookup_ms}ms), 数据大小: {data_size//1024}KB, 返回缓存数据")
                    return cached_data

                # 缓存未命中，调用原函数，记录耗时
                logger.info(f"{log_prefix} ⚠️ 缓存未命中，调用 {func.__name__}() 从数据源获取...")

                t_start = time.time()
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    elapsed = time.time() - t_start
                    logger.error(f"{log_prefix} ❌ 原函数调用异常 ({elapsed:.1f}s): {e}")
                    raise
                elapsed = time.time() - t_start

            # 检查是否有有效数据（不仅是非空 dict，还需要 data 字段有内容）
            has_valid_data = False
            data_points = 0
            if isinstance(result, dict) and isinstance(result.get('data'), list):
                data_points = len(result['data'])
                if data_points > 0:
                    has_valid_data = True

            if has_valid_data:
                # 添加缓存标记
                result["_cached"] = False
                result["_cache_timestamp"] = datetime.utcnow().isoformat()

                # 缓存结果
                logger.info(f"{log_prefix} 源数据获取完成 ({elapsed:.1f}s), 共 {data_points} 条, 正在写入缓存...")

                t_cache = time.time()
                cache_success = cache.set(code, start_date, end_date, result, ttl_days=1)
                cache_save_ms = int((time.time() - t_cache) * 1000)

                if cache_success:
                    data_size = len(str(result))
                    logger.info(f"{log_prefix} ✅ 缓存写入成功 ({cache_save_ms}ms), 数据大小: {data_size//1024}KB")
                else:
                    logger.warning(f"{log_prefix} ❌ 缓存写入失败 ({cache_save_ms}ms)")
            else:
                # 无有效数据：跳过缓存（可能是数据源全部失败，或返回空数据）
                error_detail = result.get('error', '') if isinstance(result, dict) else ''
                if error_detail:
                    logger.warning(f"{log_prefix} ⚠️ 无有效数据 ({elapsed:.1f}s), 跳过缓存 - 错误信息: {error_detail}")
                else:
                    logger.warning(f"{log_prefix} ⚠️ 无有效数据 ({elapsed:.1f}s), 跳过缓存 - 所有数据源返回空或失败")

            return result

        return wrapper

    return decorator

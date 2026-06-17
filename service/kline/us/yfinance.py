#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yfinance数据源模块
使用yfinance库获取股票K线数据，返回数据确保可 JSON 序列化
"""

import asyncio
import logging
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

from service.kline.utils import process_kline_data

logger = logging.getLogger(__name__)


def get_kline_data_from_yfinance(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    从yfinance获取K线数据（直接使用yfinance库）

    Args:
        code: 原始股票代码
        formatted_code: 格式化后的股票代码
        market_type: 市场类型 (A, HK, US)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        包含K线数据的字典，格式为:
        {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "yfinance",
            "data": processed_data
        }
        如果获取失败则返回None
    """

    try:
        # 导入yfinance
        import yfinance as yf

        # 转换日期格式为YYYY-MM-DD
        def convert_date_format(date_str):
            """将各种日期格式转换为YYYY-MM-DD格式"""
            import datetime
            formats = [
                '%Y-%m-%d',  # YYYY-MM-DD
                '%Y%m%d',    # YYYYMMDD
                '%Y/%m/%d',  # YYYY/MM/DD
                '%d/%m/%Y',  # DD/MM/YYYY
                '%m/%d/%Y',  # MM/DD/YYYY
            ]

            for fmt in formats:
                try:
                    dt = datetime.datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            # 如果所有格式都失败，返回原始字符串
            logger.warning(f"警告: 无法解析日期格式: {date_str}")
            return date_str

        # 转换开始日期和结束日期
        start_date_converted = convert_date_format(start_date)
        end_date_converted = convert_date_format(end_date)

        logger.info(f"yfinance 转换日期格式: {start_date} -> {start_date_converted}, {end_date} -> {end_date_converted}")

        # 使用download方法获取数据
        for attempt in range(2):
            try:
                # 使用download方法获取数据
                data = yf.download(
                    tickers=formatted_code,
                    start=start_date_converted,
                    end=end_date_converted,
                    interval="1d",
                    actions=False,
                    auto_adjust=False,
                    progress=False
                )

                if data is None or data.empty:
                    # 检查是否因为Rate Limit或Timeout导致返回空数据
                    if hasattr(yf.shared, '_ERRORS') and formatted_code in yf.shared._ERRORS:
                        err_info = str(yf.shared._ERRORS[formatted_code])
                        if "Too Many Requests" in err_info or "Rate limited" in err_info:
                            raise Exception(f"YFRateLimitError: {err_info}")
                        if "Timeout" in err_info or "Connection timed out" in err_info or "ConnectionError" in err_info:
                            raise Exception(f"TimeoutOrConnectionError: {err_info}")

                    logger.warning(f"yfinance 数据源返回空数据")
                    return None

                logger.info(f"yfinance 数据源成功获取数据，数据形状: {data.shape}")

                # 处理yfinance返回的多级列索引数据
                # yfinance返回的DataFrame列是元组形式，如('Close', 'AAPL')
                # 我们需要将其转换为单级列索引
                if isinstance(data.columns, pd.MultiIndex):
                    # 提取第一级列名（价格类型）
                    data = data.droplevel(level=1, axis=1)

                # 重命名列以匹配process_kline_data的期望
                column_mapping = {
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                }

                # 只重命名存在的列
                data = data.rename(columns={col: column_mapping[col] for col in data.columns if col in column_mapping})

                # 重置索引，将日期列转换为普通列
                if data.index.name == 'Date':
                    data = data.reset_index()
                    # 重命名日期列
                    data = data.rename(columns={'Date': 'date'})

                logger.info(f"处理后的数据列: {data.columns.tolist()}")

                # 处理数据
                processed_data = process_kline_data(data, 'yfinance')

                return {
                    "code": code,
                    "formatted_code": formatted_code,
                    "market": market_type,
                    "data_source": "yfinance",
                    "data": processed_data
                }

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"yfinance 数据源尝试 {attempt + 1} 失败: {error_msg}")

                # 如果是速率限制或网络错误，等待一段时间后重试
                if "Too Many Requests" in error_msg or "Rate limited" in error_msg or "Timeout" in error_msg or "Connection timed out" in error_msg or "ConnectionError" in error_msg:
                    wait_time = 5
                    logger.info(f"yfinance 请求受限或网络错误，等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(wait_time)
                    continue

                return None

        return None

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"yfinance 数据源失败: {error_msg}")
        return None


def is_yfinance_available() -> bool:
    """检查yfinance是否可用（检查yfinance库）"""
    try:
        import yfinance
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"yfinance可用: {is_yfinance_available()}")

    # 测试获取数据
    result = get_kline_data_from_yfinance(
        code="TSLA",
        formatted_code="TSLA",
        market_type="us",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )

    if result:
        print(f"成功获取数据: {result['data_source']}, 数据条数: {len(result['data'])}")
    else:
        print("获取数据失败")

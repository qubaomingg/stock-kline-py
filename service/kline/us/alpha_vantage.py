#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha Vantage数据源模块
用于从Alpha Vantage API获取股票K线数据
{
  "code": "TSLA",
  "name": "特斯拉",
  "market": "US",
  "data_source": "alpha_vantage",
  "data": [
    {
      "date": "2025-12-15",
      "open": 469.44,
      "high": 481.7694,
      "low": 467.66,
      "close": 475.31,
      "volume": 114542204
    },
    {
      "date": "2025-12-12",
      "open": 448.09,
      "high": 463.01,
      "low": 441.67,
      "close": 458.96,
      "volume": 95656749
    }
  ]
}
"""

import logging
import math
import pandas as pd
from typing import Dict, List, Optional, Any
import requests
import urllib3
import contextlib
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# 忽略SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@contextlib.contextmanager
def ignore_ssl_verification():
    """
    上下文管理器：临时禁用requests的SSL验证
    用于解决alpha_vantage调用外部接口时的SSL证书问题
    """
    original_request = requests.Session.request

    def patched_request(self, method, url, *args, **kwargs):
        kwargs['verify'] = False
        return original_request(self, method, url, *args, **kwargs)

    requests.Session.request = patched_request
    try:
        yield
    finally:
        requests.Session.request = original_request

# 导入数据处理函数
from ..utils import process_kline_data


def is_alpha_vantage_available() -> bool:
    """
    检查alpha_vantage是否可用
    """
    try:
        from alpha_vantage.timeseries import TimeSeries
        return True
    except ImportError:
        return False


def get_kline_data_from_alpha_vantage(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    从Alpha Vantage获取K线数据

    Args:
        code: 原始股票代码
        formatted_code: 格式化后的股票代码
        market_type: 市场类型
        start_date: 开始日期
        end_date: 结束日期
        api_key: API密钥

    Returns:
        包含K线数据的字典
    """

    data = None

    for attempt in range(3):
        try:
            from alpha_vantage.timeseries import TimeSeries

            # 初始化客户端
            ts = TimeSeries(key=api_key, output_format='pandas')

            # 获取数据
            # 注意：免费版API限制了outputsize='full'，使用'compact'只能获取最近100条数据
            # 如果需要获取更多数据，可能需要使用其他数据源或升级API Key
            try:
                # 使用ignore_ssl_verification上下文管理器执行API调用
                with ignore_ssl_verification():
                    # 优先尝试原始或清洗后的代码
                    # 美股代码通常是纯字母，去掉可能的市场后缀
                    clean_symbol = formatted_code.split('.')[0] if '.' in formatted_code else formatted_code

                    # 尝试多种符号格式，特别是针对优先股
                    symbols_to_try = [clean_symbol]
                    if '-' in clean_symbol:
                        # 针对 NGL-PC 这种格式，尝试多种 Alpha Vantage 可能支持的格式
                        parts = clean_symbol.split('-')
                        if len(parts) == 2:
                            base = parts[0]
                            series = parts[1]
                            # 如果 series 以 P 开头（如 PC），提取真实的系列名
                            real_series = series[1:] if series.startswith('P') else series

                            symbols_to_try.extend([
                                f"{base}PR{real_series}",   # NGLPRC
                                f"{base}.PR.{real_series}", # NGL.PR.C
                                f"{base}-P-{real_series}",  # NGL-P-C
                                f"{base}-{real_series}"      # NGL-C
                            ])

                    last_error = None
                    for sym in symbols_to_try:
                        try:
                            logger.info(f"尝试从 alpha_vantage 获取符号: {sym}")
                            data, meta_data = ts.get_daily(symbol=sym, outputsize='compact')
                            if data is not None and not data.empty:
                                logger.info(f"成功使用符号 {sym} 获取数据")
                                break
                        except ValueError as e:
                            last_error = e
                            error_msg = str(e)
                            if "Invalid API call" in error_msg:
                                continue
                            if "Our standard API call frequency" in error_msg or "Thank you for using Alpha Vantage" in error_msg:
                                # 触发限流，抛出以便外层重试
                                raise e
                            raise e
                    else:
                        if last_error:
                            raise last_error

                    if data is not None and not data.empty:
                        break # 成功获取，跳出重试循环
            except ValueError as e:
                error_msg = str(e)
                if "Our standard API call frequency" in error_msg or "Thank you for using Alpha Vantage" in error_msg:
                    # 触发限流
                    wait_time = 5 # 免费版每分钟5次，等5秒
                    logger.warning(f"alpha_vantage 速率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except Exception as e:
                error_msg = str(e)
                if "Our standard API call frequency" in error_msg or "Thank you for using Alpha Vantage" in error_msg:
                    # 触发限流
                    wait_time = 5 # 免费版每分钟5次，等5秒
                    logger.warning(f"alpha_vantage 速率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
        except Exception as e:
            logger.warning(f"alpha_vantage 数据源尝试 {attempt + 1} 失败: {e}")
            if attempt < 2:
                time.sleep(5)
                continue
            else:
                return None

    if data is None or data.empty:
        return None

    # 重命名列
    data = data.rename(columns={
        '1. open': 'open',
        '2. high': 'high',
        '3. low': 'low',
        '4. close': 'close',
        '5. volume': 'volume'
    })

    # 转换索引为日期类型
    data.index = pd.to_datetime(data.index)

    # 尝试多种日期格式解析start_date和end_date
    date_formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
    start_dt = None
    end_dt = None

    for date_format in date_formats:
        try:
            if start_dt is None:
                start_dt = datetime.strptime(start_date, date_format)
            if end_dt is None:
                end_dt = datetime.strptime(end_date, date_format)
        except ValueError:
            continue

    # 如果无法解析日期，使用默认值
    if start_dt is None:
        logger.warning(f"警告: 无法解析开始日期 {start_date}，使用默认值")
        start_dt = datetime.strptime('2000-01-01', '%Y-%m-%d')
    if end_dt is None:
        logger.warning(f"警告: 无法解析结束日期 {end_date}，使用默认值")
        end_dt = datetime.now()

    # 确保end_dt在start_dt之后
    if end_dt < start_dt:
        logger.warning(f"警告: 结束日期 {end_dt.strftime('%Y-%m-%d')} 早于开始日期 {start_dt.strftime('%Y-%m-%d')}，交换日期")
        start_dt, end_dt = end_dt, start_dt

    # 筛选日期范围
    # 注意：Alpha Vantage 返回的数据索引是 DatetimeIndex
    mask = (data.index >= start_dt) & (data.index <= end_dt)
    data = data.loc[mask]

    if data.empty:
        logger.warning(f"alpha_vantage 数据源返回空数据 (日期范围: {start_date} - {end_date})")
        return None

    # 确保数据按日期升序排列
    data = data.sort_index(ascending=True)

    logger.info(f"alpha_vantage 数据源成功获取数据，数据形状: {data.shape}")

    # 处理数据（确保可 JSON 序列化）
    processed_data = []
    for date, row in data.iterrows():
        try:
            o = float(row['open'])
            h = float(row['high'])
            l = float(row['low'])
            c = float(row['close'])
            if any(math.isnan(v) or math.isinf(v) for v in (o, h, l, c)):
                continue
            vol = row['volume']
            if pd.notna(vol):
                volume = int(vol)
            else:
                volume = 0
        except (ValueError, TypeError):
            continue
        item = {
            "date": date.strftime('%Y-%m-%d'),
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": volume,
        }
        processed_data.append(item)

    return {
        "code": code,
        "formatted_code": formatted_code,
        "market": market_type,
        "data_source": "alpha_vantage",
        "data": processed_data
    }


# 测试代码
if __name__ == "__main__":
    # 测试alpha_vantage数据源
    print("测试alpha_vantage数据源...")

    # 检查可用性
    print(f"alpha_vantage可用: {is_alpha_vantage_available()}")

    # 注意：需要设置API密钥才能实际测试
    # result = get_kline_data_from_alpha_vantage(
    #     code="AAPL",
    #     formatted_code="AAPL",
    #     market_type="us",
    #     start_date="2024-01-01",
    #     end_date="2024-01-10",
    #     api_key="your_api_key_here"
    # )
    # print(f"测试结果: {result}")

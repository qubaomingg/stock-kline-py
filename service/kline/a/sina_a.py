#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经(Sina)A股数据源模块
使用新浪财经开放API获取A股K线数据

API: https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
参数:
  - symbol: sh600519 (沪市) / sz000001 (深市)
  - scale: 240 (日线, 单位:分钟)
  - ma: no / 5,10,20 (均线)
  - datalen: 返回数据条数 (最大约2000)

返回数据格式:
  [{
    "day": "2026-05-20",
    "open": "1321.000",
    "high": "1332.990",
    "low": "1314.000",
    "close": "1315.000",
    "volume": "4748733"
  }, ...]

注意: 新浪API返回的是不复权数据
"""

from typing import Dict, List, Optional
import logging
import requests

logger = logging.getLogger(__name__)

SINA_API_URL = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
DEFAULT_TIMEOUT = 10
DEFAULT_DATALEN = 500  # 默认返回500条约2年数据
MAX_DATALEN = 2000  # 测试过最大可返回2000条

SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://finance.sina.com.cn/",
}


def _format_sina_code(code: str) -> str:
    """
    将标准股票代码转换为新浪格式
    6开头 → sh600000 (沪市)
    0开头 → sz000001 (深市)
    3开头 → sz300750 (创业板)
    8开头 → bj831305 (北交所)

    Args:
        code: 6位数字股票代码

    Returns:
        新浪格式代码 (如 sh600519)
    """
    if not code or not code.isdigit():
        return code

    if code.startswith(('6', '9')):
        return f"sh{code}"
    elif code.startswith(('0', '3', '8', '4')):
        return f"sz{code}"
    else:
        return f"sh{code}"  # 默认按沪市处理


def get_kline_data_from_sina(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str,
    datalen: int = DEFAULT_DATALEN
) -> Optional[Dict]:
    """
    从新浪财经获取A股K线数据

    Args:
        code: 原始股票代码 (如 '600519')
        formatted_code: 格式化后的股票代码 (如 '600519.SH')
        market_type: 市场类型，应为 'a'
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        datalen: 返回数据条数，默认500，最大2000

    Returns:
        包含K线数据的字典，格式为:
        {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "sina",
            "data": processed_data
        }
        如果获取失败则返回None
    """
    if market_type != 'a':
        logger.warning(f"新浪数据源仅支持A股，请求的市场类型为: {market_type}")
        return None

    try:
        sina_code = _format_sina_code(code)
        logger.info(f"使用新浪API获取A股 {code} ({sina_code}) K线数据...")

        # 新浪API按 datalen 返回最近N条，不支持精确的起止日期
        # 如果用户指定了日期范围，我们计算大概需要多少条
        actual_datalen = datalen
        if start_date and end_date:
            # 粗略估算: 一年约250个交易日
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                days_diff = (end_dt - start_dt).days
                estimated_trade_days = max(20, int(days_diff / 7 * 5 * 1.2))  # 估算交易日，加20%余量
                actual_datalen = min(MAX_DATALEN, max(datalen, estimated_trade_days))
                logger.info(f"日期范围 {start_date} ~ {end_date}, 估算需 {actual_datalen} 条数据")
            except (ValueError, ImportError):
                pass

        params = {
            "symbol": sina_code,
            "scale": 240,  # 日线（240分钟）
            "ma": "no",
            "datalen": actual_datalen
        }

        response = requests.get(
            SINA_API_URL,
            params=params,
            timeout=DEFAULT_TIMEOUT,
            headers=SINA_HEADERS
        )

        if response.status_code != 200:
            logger.warning(f"新浪API HTTP错误 {response.status_code}: {code}")
            return None

        text = response.text.strip()
        if not text or text in ['null', '[]']:
            logger.warning(f"新浪API返回空数据: {code}")
            return None

        import json
        try:
            raw_data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"新浪API返回数据格式异常: {code}, 响应: {text[:100]}")
            return None

        if not isinstance(raw_data, list) or len(raw_data) == 0:
            logger.warning(f"新浪API返回空列表: {code}")
            return None

        # 转换为标准格式，同时按日期范围过滤
        processed_data: List[Dict] = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue

            day = item.get('day', '')

            # 按日期范围过滤（如果指定了）
            if start_date and day < start_date:
                continue
            if end_date and day > end_date:
                continue

            processed_data.append({
                "date": day,
                "open": float(item.get('open', '0')),
                "high": float(item.get('high', '0')),
                "low": float(item.get('low', '0')),
                "close": float(item.get('close', '0')),
                "volume": int(float(item.get('volume', '0')))
            })

        if not processed_data:
            logger.warning(f"新浪API返回数据经日期过滤后为空: {code}, 日期范围: {start_date} ~ {end_date}")
            return None

        logger.info(f"新浪API成功获取 {code} K线数据: {len(processed_data)} 条 "
                    f"(日期范围: {processed_data[0]['date']} ~ {processed_data[-1]['date']})")

        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "sina",
            "data": processed_data
        }

    except requests.exceptions.Timeout:
        logger.warning(f"新浪API请求超时: {code}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"新浪API连接失败: {code}: {e}")
        return None
    except Exception as e:
        logger.warning(f"新浪数据源失败: {type(e).__name__}: {e}")
        return None


def is_sina_available() -> bool:
    """检查新浪API是否可用（通过简单的网络探测）"""
    try:
        response = requests.get(
            SINA_API_URL,
            params={"symbol": "sh600519", "scale": 240, "ma": "no", "datalen": 5},
            timeout=5,
            headers=SINA_HEADERS
        )
        return response.status_code == 200 and response.text.strip() not in ['null', '[]']
    except Exception:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"新浪API可用性: {is_sina_available()}")

    # 测试获取贵州茅台
    result = get_kline_data_from_sina(
        code="600519",
        formatted_code="600519.SH",
        market_type="a",
        start_date="2026-05-01",
        end_date="2026-06-16"
    )

    if result:
        print(f"\n成功获取贵州茅台: {result['data_source']}, {len(result['data'])} 条")
        print(f"日期范围: {result['data'][0]['date']} ~ {result['data'][-1]['date']}")
        print(f"最新一条: {result['data'][-1]}")
    else:
        print("获取贵州茅台失败")

    # 测试获取深南电A（之前失败的股票）
    print("\n" + "=" * 50)
    result = get_kline_data_from_sina(
        code="000037",
        formatted_code="000037.SZ",
        market_type="a",
        start_date="2026-05-01",
        end_date="2026-06-16"
    )

    if result:
        print(f"成功获取深南电A: {len(result['data'])} 条")
        print(f"日期范围: {result['data'][0]['date']} ~ {result['data'][-1]['date']}")
        print(f"最新一条: {result['data'][-1]}")
    else:
        print("获取深南电A失败")

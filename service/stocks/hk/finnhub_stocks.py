#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场 - Finnhub 数据源
使用 Finnhub API 获取港股列表，exchange="HK"
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import os
import finnhub

def get_hk_stocks_by_finnhub() -> Optional[Dict[str, Any]]:
    """
    使用 Finnhub 数据源获取港股列表

    Returns:
        包含港股股票列表的字典
    """
    try:
        print("[finnhub] 使用 Finnhub 数据源获取港股列表...")

        # 从环境变量获取 API Key
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            print("[finnhub] 警告: FINNHUB_API_KEY 环境变量未设置，跳过")
            return None

        # 初始化Finnhub客户端
        finnhub_client = finnhub.Client(api_key=api_key)

        # 获取港股列表（exchange="HK"）
        hk_stocks = finnhub_client.stock_symbols(exchange="HK")

        if not hk_stocks:
            print("[finnhub] Finnhub 数据源获取港股列表失败")
            return None

        print(f"[finnhub] 成功获取到 {len(hk_stocks)} 支原始港股")

        # 转换为标准格式，过滤非正股
        stocks = []
        for stock in hk_stocks:
            stock_type = stock.get("type", "").upper()
            symbol = stock.get("symbol", "")
            description = stock.get("description", "")

            if not symbol or not description:
                continue

            # 过滤掉基金/ETF等
            exclude_types = ["ETF", "FUND", "ETN", "TRUST", "REIT", "LP", "ETP"]
            type_excluded = any(exclude_type in stock_type for exclude_type in exclude_types)
            if type_excluded:
                continue

            # 港股代码格式化
            # Finnhub 港股通常是如 "0700.HK" 或者 "700"，我们需要标准化
            # 处理成 5 位数字，如 00700
            code = symbol.replace(".HK", "").replace("HK", "")
            code = code.zfill(5)
            if not code.isdigit():
                continue

            stock_info = {
                "code": code,
                "name": description,
                "market": "hk",
                "full_code": f"{code}.HK"
            }
            stocks.append(stock_info)

        # 去重
        unique_stocks = []
        seen_codes = set()
        for stock in stocks:
            if stock["code"] not in seen_codes:
                seen_codes.add(stock["code"])
                unique_stocks.append(stock)

        result = {
            "market": "hk",
            "count": len(unique_stocks),
            "stocks": unique_stocks,
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "finnhub"
        }

        print(f"[finnhub] 最终获取到 {len(unique_stocks)} 只港股")
        return result

    except Exception as e:
        print(f"[finnhub] 使用 Finnhub 获取港股时发生错误: {e}")
        return None


if __name__ == "__main__":
    result = get_hk_stocks_by_finnhub()
    if result:
        print(f"测试成功: {result['count']} 只港股")
        print(f"前 10 只: {result['stocks'][:10]}")
    else:
        print("测试失败")

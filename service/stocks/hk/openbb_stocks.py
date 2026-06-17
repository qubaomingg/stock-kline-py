#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场 - OpenBB 数据源
使用 OpenBB 平台获取港股列表
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from openbb import obb

def get_hk_stocks_by_openbb() -> Optional[Dict[str, Any]]:
    """
    使用 OpenBB 数据源获取港股列表

    Returns:
        包含港股股票列表的字典
    """
    try:
        print("[openbb] 使用 OpenBB 数据源获取港股列表...")

        # 方案1：尝试用 obb.equity.search
        try:
            print("[openbb] 尝试 obb.equity.search 搜索港股...")
            # 搜索港股，使用常见港股前缀
            df = obb.equity.search(query="HK", provider="yfinance")
            if not df.empty:
                print(f"[openbb] obb.equity.search 获取到 {len(df)} 条记录")
                # 筛选出港股
                hk_stocks = []
                for idx, row in df.iterrows():
                    symbol = str(row.get("symbol", ""))
                    # 检查是否是港股
                    if symbol.endswith(".HK") or "HK" in symbol:
                        name = str(row.get("name", symbol))
                        hk_stocks.append((symbol, name))
                if len(hk_stocks) > 0:
                    return _convert_to_result(hk_stocks, "search")
        except Exception as e1:
            print(f"[openbb] obb.equity.search 失败: {e1}")

        # 方案2：尝试用 obb.equity.hk（如果有的话）
        try:
            print("[openbb] 尝试查找港股相关函数...")
            # 查找所有 equity 相关函数
            eq_dir = [m for m in dir(obb.equity) if "hk" in m.lower() or "hong" in m.lower()]
            if eq_dir:
                print(f"[openbb] 找到相关函数: {eq_dir}")
        except Exception as e2:
            print(f"[openbb] 查找函数失败: {e2}")

        # 方案3：无真实数据时直接返回 None（不要生成假名称）
        print("[openbb] 所有方案都无法获取真实股票名称")
        return None
        
    except Exception as e:
        print(f"[openbb] 使用 OpenBB 获取港股时发生错误: {e}")
        return None


def _convert_to_result(hk_stocks, source_name) -> Optional[Dict[str, Any]]:
    """
    辅助函数：将港股数据转换为标准格式
    """
    stocks = []
    for code, name in hk_stocks:
        if not code or not name:
            continue
        # 港股代码标准化
        clean_code = code.replace(".HK", "").zfill(5)
        stock = {
            "code": clean_code,
            "name": name,
            "market": "hk",
            "full_code": f"{clean_code}.HK"
        }
        stocks.append(stock)
    
    result = {
        "market": "hk",
        "count": len(stocks),
        "stocks": stocks,
        "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        "source": source_name
    }
    print(f"[openbb] 最终获取到 {len(stocks)} 只港股")
    return result


if __name__ == "__main__":
    result = get_hk_stocks_by_openbb()
    if result:
        print(f"测试成功: {result['count']} 只港股")
        print(f"前 10 只: {result['stocks'][:10]}")
    else:
        print("测试失败")

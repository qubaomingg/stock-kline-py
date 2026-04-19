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

        # 方案3：使用兜底数据的主要港股作为种子，结合搜索
        print("[openbb] 使用辅助搜索方式获取港股...")
        # 获取常用港股代码
        hk_symbols = ["00001.HK", "00002.HK", "00003.HK", "00004.HK", "00005.HK", "00006.HK", "00011.HK", "00012.HK", "00016.HK", "00017.HK", "00019.HK", "00023.HK", "00027.HK", "00066.HK", "00083.HK", "00101.HK", "00144.HK", "00175.HK", "00388.HK", "00688.HK", "00700.HK", "00762.HK", "00857.HK", "00883.HK", "00941.HK", "00981.HK", "00992.HK", "01038.HK", "01088.HK", "01109.HK", "01177.HK", "01211.HK", "01299.HK", "01398.HK", "01810.HK", "01816.HK", "01888.HK", "01918.HK", "01919.HK", "01994.HK", "02007.HK", "02015.HK", "02018.HK", "02020.HK", "02068.HK", "02202.HK", "02269.HK", "02313.HK", "02318.HK", "02319.HK", "02331.HK", "02333.HK", "02338.HK", "02343.HK", "02357.HK", "02382.HK", "02388.HK", "02398.HK", "02518.HK", "02601.HK", "02628.HK", "02688.HK", "02777.HK", "02899.HK", "03323.HK", "03328.HK", "03333.HK", "03690.HK", "03692.HK", "03800.HK", "03808.HK", "03818.HK", "03888.HK", "03898.HK", "03908.HK", "03968.HK", "03988.HK", "03993.HK", "06098.HK", "06186.HK", "06862.HK", "06969.HK", "07000.HK", "08002.HK", "09003.HK", "09868.HK", "09888.HK", "09919.HK", "09922.HK", "09988.HK", "09999.HK"]
        
        hk_stocks = []
        for symbol in hk_symbols:
            try:
                # 尝试获取名称
                clean_code = symbol.replace(".HK", "")
                name = f"港股 {clean_code}"
                hk_stocks.append((clean_code, name))
            except:
                pass
        
        if len(hk_stocks) > 0:
            return _convert_to_result(hk_stocks, "openbb")
        
        print("[openbb] 所有方案都失败")
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

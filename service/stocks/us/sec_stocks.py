"""
SEC 数据源美股列表获取模块
使用 OpenBB 的 SEC 数据源获取美股列表
{
  "market": "us",
  "count": 10221,
  "stocks": [
    {
      "code": "NVDA",
      "name": "NVIDIA CORP",
      "market": "us",
      "full_code": "NVDA.US"
    }
  ]
}
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from openbb import obb


def get_sec_stocks(exchange: str = "N") -> Optional[Dict[str, Any]]:
    """
    使用 SEC 数据源获取美股列表
    
    Args:
        exchange: 交易所代码
            - N=Nasdaq
            - A=NYSE
            - P=AMEX
            
    Returns:
        包含美股股票列表的字典
    """
    try:
        print(f"使用 SEC 数据源获取 {exchange} 交易所的美股列表...")
        
        # 使用 SEC 数据源获取股票列表
        result_df = obb.equity.search(
            exchange=exchange,
            is_fund=False,  # 排除基金/ETF
            provider="sec"  # SEC 数据源，免费无需密钥
        ).to_df()
        
        if result_df.empty:
            print(f"SEC 数据源获取 {exchange} 交易所股票列表失败")
            return None
        
        print(f"SEC 数据源获取到 {len(result_df)} 支股票")
        
        # 转换为标准格式
        stocks = []
        for _, row in result_df.iterrows():
            stock_info = {
                "code": row.get("symbol", ""),
                "name": row.get("name", ""),
                "market": "us",
                "full_code": f"{row.get('symbol', '')}.US"
            }
            stocks.append(stock_info)
        
        return {
            "market": "us",
            "count": len(stocks),
            "stocks": stocks,
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "sec"
        }
        
    except Exception as e:
        print(f"SEC 数据源获取美股列表时发生错误: {e}")
        return None


def get_sec_stocks_all() -> Optional[Dict[str, Any]]:
    """
    获取所有交易所的美股列表（合并 Nasdaq、NYSE、AMEX）
    
    Returns:
        包含所有美股股票列表的字典
    """
    try:
        all_stocks = []
        
        # 获取三个主要交易所的股票
        exchanges = ["N", "A", "P"]
        exchange_names = {"N": "Nasdaq", "A": "NYSE", "P": "AMEX"}
        
        for exchange in exchanges:
            print(f"获取 {exchange_names[exchange]} 交易所股票...")
            result = get_sec_stocks(exchange)
            if result and result["stocks"]:
                all_stocks.extend(result["stocks"])
                print(f"  获取到 {len(result['stocks'])} 支股票")
            else:
                print(f"  获取失败")
        
        if not all_stocks:
            print("所有交易所获取失败")
            return None
        
        # 去重（按股票代码）
        unique_stocks = []
        seen_codes = set()
        for stock in all_stocks:
            if stock["code"] not in seen_codes:
                seen_codes.add(stock["code"])
                unique_stocks.append(stock)
        
        print(f"合并后共获取到 {len(unique_stocks)} 支唯一股票")
        
        return {
            "market": "us",
            "count": len(unique_stocks),
            "stocks": unique_stocks,
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "sec"
        }
        
    except Exception as e:
        print(f"获取所有交易所美股列表时发生错误: {e}")
        return None


if __name__ == "__main__":
    # 测试 SEC 数据源
    print("测试 SEC 数据源:")
    
    # 测试单个交易所
    print("\n测试 Nasdaq 交易所:")
    result = get_sec_stocks("N")
    if result:
        print(f"获取到 {result['count']} 只股票")
        if result["stocks"]:
            print("前5只股票:")
            for stock in result["stocks"][:5]:
                print(f"  {stock['code']}: {stock['name']}")
    else:
        print("获取失败")
    
    # 测试所有交易所
    print("\n测试所有交易所:")
    result = get_sec_stocks_all()
    if result:
        print(f"获取到 {result['count']} 只唯一股票")
    else:
        print("获取失败")
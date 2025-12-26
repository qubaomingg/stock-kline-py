#!/usr/bin/env python3
"""
Finnhub 数据源美股列表获取模块
使用 Finnhub API 获取美股列表
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

import os
import pandas as pd
from typing import Dict, Any, Optional, List
import finnhub


def get_finnhub_stocks(exchange: str = "US") -> Optional[Dict[str, Any]]:
    """
    使用 Finnhub 数据源获取美股列表
    
    Args:
        exchange: 交易所代码
            - US=美国市场
            - 其他交易所代码参考 Finnhub 文档
            
    Returns:
        包含美股股票列表的字典
    """
    try:
        print(f"使用 Finnhub 数据源获取 {exchange} 交易所的美股列表...")
        
        # 从环境变量获取 API Key
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            print("警告: FINNHUB_API_KEY 环境变量未设置，使用默认测试密钥（可能受限）")
            api_key = "YOUR_FINNHUB_API_KEY"  # 需要用户设置环境变量
        
        # 初始化Finnhub客户端
        finnhub_client = finnhub.Client(api_key=api_key)
        
        # 获取美股列表
        us_stocks = finnhub_client.stock_symbols(exchange=exchange)
        
        if not us_stocks:
            print(f"Finnhub 数据源获取 {exchange} 交易所股票列表失败")
            return None
        
        print(f"Finnhub 数据源获取到 {len(us_stocks)} 支股票")
        
        # 转换为标准格式
        stocks = []
        for stock in us_stocks:
            # 过滤掉基金/ETF等非正股
            stock_type = stock.get("type", "").upper()
            symbol = stock.get("symbol", "")
            description = stock.get("description", "")
            
            # 排除条件：
            # 1. type字段包含ETF、FUND、ETN等
            # 2. 股票代码包含特殊后缀（如.PR, .RT, .WI等）
            # 3. 描述中包含基金、ETF等关键词
            # 4. 股票代码以F、X、Z、Y、V、Q结尾（通常是外国公司或特殊类型）
            # 5. NVDR类型（非投票权存托凭证）
            # 6. UNIT类型（单位信托）
            exclude_types = ["ETF", "FUND", "ETN", "TRUST", "REIT", "LP", "ETP", "CLOSED-END FUND", "EQUITY WRT", "PREFERENCE", "PUBLIC", "NVDR", "UNIT"]
            exclude_suffixes = [".PR", ".RT", ".WI", ".UN", ".UNT", ".UNIT", ".V", ".W", ".U", ".PRA", ".PRB"]
            exclude_keywords = ["ETF", "FUND", "TRUST", "REIT", "PARTNERSHIP", "LIMITED PARTNERSHIP", "CLOSED-END FUND", "EQUITY WRT", "PREFERENCE", "BOND", "NVDR", "UNIT"]
            exclude_symbol_endings = ["F", "X", "Z", "Y", "V", "Q"]
            
            # 检查type字段
            type_excluded = any(exclude_type in stock_type for exclude_type in exclude_types)
            
            # 检查股票代码后缀
            suffix_excluded = any(symbol.upper().endswith(suffix) for suffix in exclude_suffixes)
            
            # 检查描述中的关键词
            desc_excluded = any(keyword in description.upper() for keyword in exclude_keywords)
            
            # 检查股票代码结尾
            symbol_ending_excluded = any(symbol.upper().endswith(ending) for ending in exclude_symbol_endings)
            
            # 如果满足任何排除条件，跳过
            if type_excluded or suffix_excluded or desc_excluded or symbol_ending_excluded:
                continue
                
            stock_info = {
                "code": symbol,
                "name": description,
                "market": "us",
                "full_code": f"{symbol}.US"
            }
            stocks.append(stock_info)
        
        return {
            "market": "us",
            "count": len(stocks),
            "stocks": stocks,
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "finnhub"
        }
        
    except Exception as e:
        print(f"Finnhub 数据源获取美股列表时发生错误: {e}")
        return None


def get_finnhub_stocks_all() -> Optional[Dict[str, Any]]:
    """
    获取所有交易所的美股列表（合并多个交易所）
    
    Returns:
        包含所有美股股票列表的字典
    """
    try:
        all_stocks = []
        
        # 获取美国主要交易所的股票
        exchanges = ["US"]  # Finnhub 使用 "US" 代表美国市场
        
        for exchange in exchanges:
            print(f"获取 {exchange} 交易所股票...")
            result = get_finnhub_stocks(exchange)
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
            "source": "finnhub"
        }
        
    except Exception as e:
        print(f"获取所有交易所美股列表时发生错误: {e}")
        return None
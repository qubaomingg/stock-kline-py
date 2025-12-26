#!/usr/bin/env python3
"""
分析Finnhub API返回的股票数据，找出需要过滤的类型
"""

import os
import finnhub
from typing import List, Dict, Any

def analyze_finnhub_stocks():
    """分析Finnhub API返回的股票数据"""
    try:
        # 从.env文件加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        # 从环境变量获取 API Key
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            print("错误: FINNHUB_API_KEY 环境变量未设置，请检查.env文件")
            return
        
        # 初始化Finnhub客户端
        finnhub_client = finnhub.Client(api_key=api_key)
        
        # 获取美股列表
        us_stocks = finnhub_client.stock_symbols(exchange="US")
        
        if not us_stocks:
            print("Finnhub 数据源获取股票列表失败")
            return
        
        print(f"原始数据共 {len(us_stocks)} 支股票")
        
        # 统计不同类型的股票
        type_counter = {}
        symbol_patterns = {}
        description_keywords = {}
        
        # 分析前100支股票
        sample_size = min(100, len(us_stocks))
        print(f"\n分析前 {sample_size} 支股票样本：")
        
        for i, stock in enumerate(us_stocks[:sample_size]):
            stock_type = stock.get("type", "").upper()
            symbol = stock.get("symbol", "")
            description = stock.get("description", "")
            
            # 统计type类型
            if stock_type:
                type_counter[stock_type] = type_counter.get(stock_type, 0) + 1
            
            # 分析股票代码模式
            if symbol:
                # 检查特殊后缀
                if "." in symbol:
                    suffix = symbol.split(".")[-1]
                    symbol_patterns[f".{suffix}"] = symbol_patterns.get(f".{suffix}", 0) + 1
                # 检查其他模式
                elif symbol.endswith("X"):
                    symbol_patterns["X结尾"] = symbol_patterns.get("X结尾", 0) + 1
                elif symbol.endswith("W"):
                    symbol_patterns["W结尾"] = symbol_patterns.get("W结尾", 0) + 1
                elif symbol.endswith("U"):
                    symbol_patterns["U结尾"] = symbol_patterns.get("U结尾", 0) + 1
            
            # 分析描述中的关键词
            desc_upper = description.upper()
            keywords = ["ETF", "FUND", "TRUST", "REIT", "PARTNERSHIP", 
                       "LIMITED", "ADR", "ETN", "NOTE", "BOND", 
                       "DEBT", "PREFERRED", "COMMON", "SHARES", "STOCK"]
            
            for keyword in keywords:
                if keyword in desc_upper:
                    description_keywords[keyword] = description_keywords.get(keyword, 0) + 1
        
        # 打印统计结果
        print("\n=== 股票类型统计 ===")
        for type_name, count in sorted(type_counter.items(), key=lambda x: x[1], reverse=True):
            print(f"  {type_name}: {count}")
        
        print("\n=== 股票代码模式统计 ===")
        for pattern, count in sorted(symbol_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern}: {count}")
        
        print("\n=== 描述关键词统计 ===")
        for keyword, count in sorted(description_keywords.items(), key=lambda x: x[1], reverse=True):
            print(f"  {keyword}: {count}")
        
        # 显示一些需要过滤的示例
        print("\n=== 需要过滤的股票示例 ===")
        filtered_examples = []
        for stock in us_stocks[:50]:
            stock_type = stock.get("type", "").upper()
            symbol = stock.get("symbol", "")
            description = stock.get("description", "")
            
            # 检查是否需要过滤
            exclude_types = ["ETF", "FUND", "ETN", "TRUST", "REIT", "LP", "ADR", "PREFERRED"]
            exclude_suffixes = [".PR", ".RT", ".WI", ".UN", ".UNT", ".UNIT", ".V", ".W", ".U", ".A", ".B", ".C"]
            
            type_excluded = any(exclude_type in stock_type for exclude_type in exclude_types)
            suffix_excluded = any(symbol.upper().endswith(suffix) for suffix in exclude_suffixes)
            
            if type_excluded or suffix_excluded:
                filtered_examples.append({
                    "symbol": symbol,
                    "type": stock_type,
                    "description": description[:50] + "..." if len(description) > 50 else description
                })
                
                if len(filtered_examples) >= 10:
                    break
        
        for example in filtered_examples:
            print(f"  代码: {example['symbol']}, 类型: {example['type']}, 描述: {example['description']}")
        
        # 显示一些应该保留的示例
        print("\n=== 应该保留的股票示例 ===")
        kept_examples = []
        for stock in us_stocks[:50]:
            stock_type = stock.get("type", "").upper()
            symbol = stock.get("symbol", "")
            description = stock.get("description", "")
            
            # 检查是否应该保留
            keep_types = ["COMMON", "ORDINARY", "SHARES", "STOCK"]
            
            type_kept = any(keep_type in stock_type for keep_type in keep_types)
            
            if type_kept and "." not in symbol:
                kept_examples.append({
                    "symbol": symbol,
                    "type": stock_type,
                    "description": description[:50] + "..." if len(description) > 50 else description
                })
                
                if len(kept_examples) >= 10:
                    break
        
        for example in kept_examples:
            print(f"  代码: {example['symbol']}, 类型: {example['type']}, 描述: {example['description']}")
        
    except Exception as e:
        print(f"分析Finnhub数据时发生错误: {e}")

if __name__ == "__main__":
    analyze_finnhub_stocks()
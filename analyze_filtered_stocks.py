#!/usr/bin/env python3
"""
分析过滤后的股票，找出还需要过滤的类型
"""

import os
import sys
import finnhub
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

def analyze_filtered_stocks():
    """分析过滤后的股票"""
    try:
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
        
        # 应用当前过滤逻辑
        filtered_stocks = []
        excluded_stocks = []
        
        exclude_types = ["ETF", "FUND", "ETN", "TRUST", "REIT", "LP", "ADR", "ETP", "CLOSED-END FUND", "EQUITY WRT", "PREFERENCE", "PUBLIC"]
        exclude_suffixes = [".PR", ".RT", ".WI", ".UN", ".UNT", ".UNIT", ".V", ".W", ".U", ".PRA", ".PRB"]
        exclude_keywords = ["ETF", "FUND", "TRUST", "REIT", "PARTNERSHIP", "LIMITED PARTNERSHIP", "ADR", "CLOSED-END FUND", "EQUITY WRT", "PREFERENCE", "BOND"]
        
        for stock in us_stocks:
            stock_type = stock.get("type", "").upper()
            symbol = stock.get("symbol", "")
            description = stock.get("description", "")
            
            # 检查type字段
            type_excluded = any(exclude_type in stock_type for exclude_type in exclude_types)
            
            # 检查股票代码后缀
            suffix_excluded = any(symbol.upper().endswith(suffix) for suffix in exclude_suffixes)
            
            # 检查描述中的关键词
            desc_excluded = any(keyword in description.upper() for keyword in exclude_keywords)
            
            # 如果满足任何排除条件，记录排除原因
            if type_excluded or suffix_excluded or desc_excluded:
                reason = []
                if type_excluded:
                    reason.append(f"type: {stock_type}")
                if suffix_excluded:
                    reason.append(f"suffix: {symbol}")
                if desc_excluded:
                    reason.append(f"desc: {description[:50]}...")
                excluded_stocks.append({
                    "symbol": symbol,
                    "type": stock_type,
                    "description": description,
                    "reason": ", ".join(reason)
                })
            else:
                filtered_stocks.append(stock)
        
        print(f"过滤后股票数量: {len(filtered_stocks)}")
        print(f"排除股票数量: {len(excluded_stocks)}")
        
        # 分析过滤后的股票类型
        print("\n=== 过滤后股票类型分析 ===")
        filtered_types = {}
        for stock in filtered_stocks[:100]:  # 分析前100支
            stock_type = stock.get("type", "").upper()
            if stock_type:
                filtered_types[stock_type] = filtered_types.get(stock_type, 0) + 1
        
        for type_name, count in sorted(filtered_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {type_name}: {count}")
        
        # 分析过滤后股票的代码模式
        print("\n=== 过滤后股票代码模式分析 ===")
        symbol_patterns = {}
        for stock in filtered_stocks[:100]:
            symbol = stock.get("symbol", "")
            if symbol:
                # 检查特殊后缀
                for suffix in ["F", "Y", "Z", "Q", "X", "W", "V", "U"]:
                    if symbol.endswith(suffix):
                        symbol_patterns[suffix] = symbol_patterns.get(suffix, 0) + 1
                        break
        
        for suffix, count in sorted(symbol_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  {suffix}结尾: {count}")
        
        # 显示一些过滤后的股票示例
        print("\n=== 过滤后股票示例 ===")
        for i, stock in enumerate(filtered_stocks[:10]):
            print(f"  {i+1}. {stock.get('symbol')} - {stock.get('type')} - {stock.get('description')[:50]}...")
        
        # 显示一些被排除的股票示例
        print("\n=== 被排除股票示例 ===")
        for i, stock in enumerate(excluded_stocks[:10]):
            print(f"  {i+1}. {stock['symbol']} - {stock['type']} - {stock['reason']}")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")

if __name__ == "__main__":
    analyze_filtered_stocks()
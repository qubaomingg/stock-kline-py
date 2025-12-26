#!/usr/bin/env python3
"""
测试yfinance数据源
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from service.stocks.us.yfinance_stocks import get_yfinance_stocks, get_yfinance_stocks_all

print("测试yfinance数据源")
print("=" * 50)

print("\n1. 测试 NYSE 交易所:")
result = get_yfinance_stocks("nyse")
if result:
    print(f"✓ 成功获取到 {result['count']} 只股票")
    if result["stocks"]:
        print("前5只股票:")
        for stock in result["stocks"][:5]:
            print(f"  {stock['code']}: {stock['name']} ({stock.get('exchange', 'N/A')})")
else:
    print("✗ 获取失败")

print("\n2. 测试 Nasdaq 交易所:")
result = get_yfinance_stocks("nasdaq")
if result:
    print(f"✓ 成功获取到 {result['count']} 只股票")
    if result["stocks"]:
        print("前5只股票:")
        for stock in result["stocks"][:5]:
            print(f"  {stock['code']}: {stock['name']} ({stock.get('exchange', 'N/A')})")
else:
    print("✗ 获取失败")

print("\n3. 测试 AMEX 交易所:")
result = get_yfinance_stocks("amex")
if result:
    print(f"✓ 成功获取到 {result['count']} 只股票")
    if result["stocks"]:
        print("前5只股票:")
        for stock in result["stocks"][:5]:
            print(f"  {stock['code']}: {stock['name']} ({stock.get('exchange', 'N/A')})")
else:
    print("✗ 获取失败")

print("\n4. 测试获取所有交易所:")
result = get_yfinance_stocks_all()
if result:
    print(f"✓ 成功获取到 {result['count']} 只股票（去重后）")
    if result["stocks"]:
        print("前10只股票:")
        for stock in result["stocks"][:10]:
            print(f"  {stock['code']}: {stock['name']} ({stock.get('exchange', 'N/A')})")
        
        # 统计各交易所股票数量
        exchanges = {}
        for stock in result["stocks"]:
            exchange = stock.get('exchange', 'Unknown')
            exchanges[exchange] = exchanges.get(exchange, 0) + 1
        
        print("\n各交易所股票数量:")
        for exchange, count in exchanges.items():
            print(f"  {exchange}: {count} 只")
else:
    print("✗ 获取失败")

print("\n测试完成")
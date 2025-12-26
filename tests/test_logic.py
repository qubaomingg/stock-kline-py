#!/usr/bin/env python3
"""
测试 us_stocks.py 的逻辑：验证一个数据源成功获取后不再尝试后续数据源
"""

import sys
sys.path.insert(0, '.')

from service.stocks.us.us_stocks import get_us_stocks, get_us_stocks_by_exchange

print("测试逻辑：一个数据源成功获取后是否继续尝试后续数据源")
print("=" * 60)

print("\n1. 测试 get_us_stocks() 按优先级获取:")
print("   如果 sec 成功，应该不会尝试 yfinance 和 fmp")
result = get_us_stocks()
if result:
    print(f"   成功获取到 {result['count']} 只股票，数据源: {result.get('source', 'unknown')}")
else:
    print("   所有数据源都失败了")

print("\n2. 测试 get_us_stocks_by_exchange('N') 按优先级获取:")
print("   如果 sec 成功，应该不会尝试 yfinance 和 fmp")
result = get_us_stocks_by_exchange('N')
if result:
    print(f"   成功获取到 {result['count']} 只股票，数据源: {result.get('source', 'unknown')}")
else:
    print("   所有数据源都失败了")

print("\n3. 测试指定数据源 sec:")
result = get_us_stocks(data_source='sec')
if result:
    print(f"   sec 数据源获取到 {result['count']} 只股票")
else:
    print("   sec 数据源获取失败")

print("\n测试完成！观察输出日志，确认是否在成功获取后继续尝试其他数据源。")
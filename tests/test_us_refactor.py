#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的美股获取功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.stocks.stocks import get_stock_by_market
from service.stocks.us.us_stocks import get_us_stocks, get_us_stocks_by_exchange


def test_us_stocks():
    """测试美股获取功能"""
    print("\n1. 测试通过 stocks.py 获取美股:")
    result = get_stock_by_market('us')
    if result:
        print(f"   获取成功: {result['count']} 只股票")
        print(f"   市场: {result.get('market', 'unknown')}")
        print(f"   时间戳: {result.get('timestamp', 'unknown')}")
        if result.get('stocks'):
            print(f"   前3只股票:")
            for i, stock in enumerate(result['stocks'][:3], 1):
                print(f"     {i}. {stock.get('code', 'N/A')}: {stock.get('name', 'N/A')}")
    else:
        print("   获取失败")


def test_us_stocks_direct():
    """直接测试 us_stocks.py"""
    print("\n2. 直接测试 us_stocks.py:")
    
    # 测试按优先级获取
    print("   a) 按优先级获取:")
    result = get_us_stocks()
    if result:
        print(f"      获取成功: {result['count']} 只股票")
        print(f"      数据源: {result.get('source', 'unknown')}")
    else:
        print("      获取失败")
    
    # 测试各个数据源
    print("   b) 测试各个数据源:")
    for source in ['sec', 'yfinance', 'fmp']:
        result = get_us_stocks(data_source=source)
        if result:
            print(f"      {source}: {result['count']} 只股票")
        else:
            print(f"      {source}: 获取失败")


def test_us_stocks_by_exchange():
    """测试按交易所获取"""
    print("\n3. 测试按交易所获取:")
    
    # 测试 sec 数据源
    print("   a) sec 数据源:")
    for exchange in ["N", "A", "P"]:
        result = get_us_stocks_by_exchange(exchange, data_source="sec")
        if result:
            print(f"      {exchange}: {result['count']} 只股票")
        else:
            print(f"      {exchange}: 获取失败")
    
    # 测试 yfinance 数据源
    print("   b) yfinance 数据源:")
    for exchange in ["nasdaq", "nyse", "amex"]:
        result = get_us_stocks_by_exchange(exchange, data_source="yfinance")
        if result:
            print(f"      {exchange}: {result['count']} 只股票")
        else:
            print(f"      {exchange}: 获取失败")


def main():
    """主函数"""
    print("开始测试重构后的美股获取功能...")
    
    try:
        test_us_stocks()
        test_us_stocks_direct()
        test_us_stocks_by_exchange()
        
        print("\n测试完成!")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
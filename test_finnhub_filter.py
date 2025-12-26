#!/usr/bin/env python3
"""
测试Finnhub数据过滤逻辑
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from service.stocks.us.finnhub_stocks import get_finnhub_stocks

def test_finnhub_filter():
    """测试Finnhub数据过滤"""
    print("测试Finnhub数据过滤逻辑...")
    
    # 获取过滤后的股票数据
    result = get_finnhub_stocks(exchange="US")
    
    if not result:
        print("获取数据失败")
        return
    
    print(f"过滤后股票数量: {result['count']}")
    print(f"数据源: {result['source']}")
    print(f"时间戳: {result['timestamp']}")
    
    # 显示前10支股票
    print("\n前10支股票:")
    for i, stock in enumerate(result['stocks'][:10]):
        print(f"  {i+1}. {stock['code']} - {stock['name']}")
    
    # 统计信息
    print("\n=== 统计信息 ===")
    print(f"原始数据: 29829 支股票")
    print(f"过滤后: {result['count']} 支股票")
    print(f"过滤掉: {29829 - result['count']} 支股票")
    print(f"保留比例: {result['count']/29829*100:.2f}%")

if __name__ == "__main__":
    test_finnhub_filter()
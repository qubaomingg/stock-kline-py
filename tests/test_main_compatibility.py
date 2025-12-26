#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

# 模拟 main.py 中的代码逻辑
print("测试 main.py 兼容性...")

# 导入 stocks 模块
from service.stocks.stocks import get_stock_by_market

# 测试 main.py 中可能访问的字段
markets = ['us', 'cn', 'hk']

for market in markets:
    print(f"\n测试市场: {market}")
    result = get_stock_by_market(market)
    
    if result:
        # 模拟 main.py 中可能访问的字段
        try:
            # 检查 timestamp 字段是否存在（这是用户关心的）
            timestamp = result.get('timestamp')
            print(f"  timestamp 字段存在: {timestamp}")
            
            # 检查其他可能访问的字段
            market_field = result.get('market')
            count = result.get('count')
            stocks = result.get('stocks')
            
            print(f"  market 字段存在: {market_field}")
            print(f"  count 字段存在: {count}")
            print(f"  stocks 字段存在: {len(stocks) if stocks else 0} 条记录")
            
            # 检查 stocks 中的字段结构
            if stocks and len(stocks) > 0:
                first_stock = stocks[0]
                print(f"  第一个股票包含字段: {list(first_stock.keys())}")
                
        except Exception as e:
            print(f"  访问字段时出错: {e}")
    else:
        print(f"  获取 {market} 市场数据失败")

print("\n兼容性测试完成！")
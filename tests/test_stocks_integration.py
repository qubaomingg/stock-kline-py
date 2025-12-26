#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from service.stocks.stocks import get_stock_by_market

print("测试 stocks.py 中的 get_stock_by_market 函数...")

# 测试美股市场
print("\n1. 测试美股市场 (market='us'):")
result = get_stock_by_market('us')
print(f"Result type: {type(result)}")
if result:
    print(f"Keys: {list(result.keys())}")
    print(f"Market: {result.get('market')}")
    print(f"Count: {result.get('count')}")
    print(f"Timestamp: {result.get('timestamp')}")
    
    # 检查是否包含必要的字段
    required_fields = ['market', 'count', 'stocks', 'timestamp']
    missing_fields = [field for field in required_fields if field not in result]
    
    if missing_fields:
        print(f"警告: 缺少以下字段: {missing_fields}")
    else:
        print("成功: 所有必需字段都存在")
        
        # 检查 stocks 字段
        if result['stocks']:
            print(f"Stocks 数量: {len(result['stocks'])}")
            if len(result['stocks']) > 0:
                print("第一个股票信息:")
                first_stock = result['stocks'][0]
                print(f"  代码: {first_stock.get('code')}")
                print(f"  名称: {first_stock.get('name')}")
                print(f"  市场: {first_stock.get('market')}")
                print(f"  完整代码: {first_stock.get('full_code')}")
else:
    print("获取美股市场结果失败")

# 测试A股市场
print("\n2. 测试A股市场 (market='cn'):")
result = get_stock_by_market('cn')
print(f"Result type: {type(result)}")
if result:
    print(f"Keys: {list(result.keys())}")
    print(f"Market: {result.get('market')}")
    print(f"Count: {result.get('count')}")
    print(f"Timestamp: {result.get('timestamp')}")
    print(f"Stocks 数量: {len(result['stocks']) if result.get('stocks') else 0}")
else:
    print("获取A股市场结果失败")

# 测试港股市场
print("\n3. 测试港股市场 (market='hk'):")
result = get_stock_by_market('hk')
print(f"Result type: {type(result)}")
if result:
    print(f"Keys: {list(result.keys())}")
    print(f"Market: {result.get('market')}")
    print(f"Count: {result.get('count')}")
    print(f"Timestamp: {result.get('timestamp')}")
    print(f"Stocks 数量: {len(result['stocks']) if result.get('stocks') else 0}")
else:
    print("获取港股市场结果失败")

# 测试无效市场
print("\n4. 测试无效市场 (market='invalid'):")
result = get_stock_by_market('invalid')
print(f"Result: {result}")
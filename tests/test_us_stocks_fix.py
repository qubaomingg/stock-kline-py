#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from service.stocks.us.us_stocks import get_us_stocks

print("测试 us_stocks.py 修复后的功能...")
result = get_us_stocks()

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
        print(f"\n警告: 缺少以下字段: {missing_fields}")
    else:
        print("\n成功: 所有必需字段都存在")
        
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
    print("获取结果失败")
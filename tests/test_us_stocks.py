#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试美股股票列表获取
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.stocks.us.us_stocks import get_us_stocks

if __name__ == "__main__":
    print("开始测试美股股票列表获取...")
    
    result = get_us_stocks()
    
    print(f"结果类型: {type(result)}")
    
    if result:
        print(f"市场: {result['market']}")
        print(f"股票数量: {result['count']}")
        print(f"数据源: {result['source']}")
        print(f"时间戳: {result['timestamp']}")
        
        if result['stocks']:
            print("\n前10只股票:")
            for i, stock in enumerate(result['stocks'][:10]):
                print(f"  {i+1}. {stock['code']} - {stock['name']} - {stock.get('industry', 'N/A')}")
    else:
        print("获取美股列表失败")
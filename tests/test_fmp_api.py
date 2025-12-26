#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试FMP API密钥加载和美股列表获取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.stocks.us.us_stocks import get_us_stocks

if __name__ == "__main__":
    print("测试FMP API密钥加载和美股列表获取...")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"FMP_API_KEY环境变量: {os.getenv('FMP_API_KEY')}")
    
    result = get_us_stocks()
    
    print(f"\n结果类型: {type(result)}")
    if result:
        print(f"市场: {result.get('market')}")
        print(f"股票数量: {result.get('count')}")
        stocks = result.get('stocks', [])
        if stocks:
            print(f"前3只股票: {stocks[:3]}")
        else:
            print("股票列表为空")
        print(f"时间戳: {result.get('timestamp')}")
        print(f"数据源: {result.get('source')}")
    else:
        print("结果为None")
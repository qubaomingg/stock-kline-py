#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试A股eastmoney_stocks.py模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eastmoney_stocks import get_cn_stocks_by_eastmoney

def main():
    print("开始测试A股eastmoney数据源...")
    
    result = get_cn_stocks_by_eastmoney()
    
    if result:
        print(f"\n测试成功!")
        print(f"市场: {result['market']}")
        print(f"数据源: {result['source']}")
        print(f"时间戳: {result['timestamp']}")
        print(f"股票数量: {result['count']}只")
        
        if result['stocks']:
            print(f"\n前10只股票:")
            for i, stock in enumerate(result['stocks'][:10]):
                print(f"  {i+1:2d}. {stock['code']:6s} {stock['name']:10s} {stock['full_code']:10s}")
            
            print(f"\n最后10只股票:")
            for i, stock in enumerate(result['stocks'][-10:]):
                idx = result['count'] - 10 + i + 1
                print(f"  {idx:2d}. {stock['code']:6s} {stock['name']:10s} {stock['full_code']:10s}")
    else:
        print("\n测试失败: 获取A股股票列表失败")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
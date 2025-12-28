#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试cn_stocks.py集成eastmoney数据源
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cn_stocks import get_cn_stocks

def main():
    print("开始测试cn_stocks.py集成eastmoney数据源...")
    
    result = get_cn_stocks()
    
    if result:
        print(f"\n测试成功!")
        print(f"市场: {result['market']}")
        print(f"数据源: {result['source']}")
        print(f"时间戳: {result['timestamp']}")
        print(f"股票数量: {result['count']}只")
        
        if result['stocks']:
            print(f"\n前5只股票:")
            for i, stock in enumerate(result['stocks'][:5]):
                print(f"  {i+1:2d}. {stock['code']:6s} {stock['name']:10s} {stock['full_code']:10s}")
            
            # 验证数据源优先级
            if result['source'] == 'eastmoney':
                print(f"\n✓ 数据源优先级正确: 使用了eastmoney数据源")
            else:
                print(f"\n⚠ 使用了其他数据源: {result['source']}")
    else:
        print("\n测试失败: 获取A股股票列表失败")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
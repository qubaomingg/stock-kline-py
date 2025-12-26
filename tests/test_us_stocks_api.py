#!/usr/bin/env python3
"""
测试us_stocks.py中的get_us_stocks函数
"""

import sys
import os
sys.path.append('.')

from service.stocks.us.us_stocks import get_us_stocks

if __name__ == "__main__":
    print("正在测试get_us_stocks函数...")
    
    try:
        result = get_us_stocks()
        
        if result:
            print(f"✓ 成功获取美股列表")
            print(f"  股票数量: {result['count']}")
            print(f"  数据来源: {result['source']}")
            print(f"  时间戳: {result['timestamp']}")
            
            # 显示前5只股票
            print("\n前5只股票:")
            for i, stock in enumerate(result['stocks'][:5], 1):
                print(f"  {i}. {stock['code']} - {stock['name']}")
        else:
            print("✗ 获取美股列表失败")
            
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
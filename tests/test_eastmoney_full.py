#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的eastmoney_stocks.py，验证分页获取所有港股
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.stocks.hk.eastmoney_stocks import get_hk_stocks_by_eastmoney

def test_eastmoney_full():
    """测试分页获取所有港股"""
    print("测试分页获取所有港股...")
    
    result = get_hk_stocks_by_eastmoney()
    
    if result:
        print(f"\n✅ 成功获取港股数据")
        print(f"市场: {result['market']}")
        print(f"数据源: {result['source']}")
        print(f"时间戳: {result['timestamp']}")
        print(f"股票数量: {result['count']}")
        
        # 显示前10只股票
        print(f"\n前10只股票:")
        for i, stock in enumerate(result['stocks'][:10], 1):
            print(f"  {i:2d}. {stock['code']:8s} - {stock['name']}")
        
        # 显示最后10只股票
        print(f"\n最后10只股票:")
        for i, stock in enumerate(result['stocks'][-10:], result['count']-9):
            print(f"  {i:2d}. {stock['code']:8s} - {stock['name']}")
        
        # 统计信息
        print(f"\n📊 统计信息:")
        print(f"  总股票数: {result['count']}")
        print(f"  预期总数: 2847 (根据API返回)")
        
        if result['count'] >= 2800:
            print(f"  ✅ 成功获取大部分港股数据")
        else:
            print(f"  ⚠️ 获取数量偏少，可能仍有分页问题")
    else:
        print("❌ 获取港股数据失败")
    
    return result

if __name__ == "__main__":
    test_eastmoney_full()
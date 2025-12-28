#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试东方财富API数据源
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eastmoney_stocks import get_hk_stocks_by_eastmoney

def test_eastmoney_api():
    """测试东方财富API获取港股列表"""
    print("测试东方财富API数据源...")
    
    result = get_hk_stocks_by_eastmoney()
    
    if result:
        print(f"✅ 成功获取港股列表")
        print(f"   数据源: {result['source']}")
        print(f"   股票数量: {result['count']}")
        print(f"   时间戳: {result['timestamp']}")
        
        # 显示前5只股票
        print("\n前5只股票:")
        for i, stock in enumerate(result['stocks'][:5]):
            print(f"   {i+1}. {stock['code']} - {stock['name']} ({stock['full_code']})")
        
        return True
    else:
        print("❌ 获取港股列表失败")
        return False

if __name__ == "__main__":
    success = test_eastmoney_api()
    sys.exit(0 if success else 1)
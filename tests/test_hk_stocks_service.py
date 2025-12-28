#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试港股股票列表服务
"""

import sys
import os

# 添加服务目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service/stocks/hk'))

from hk_stocks import get_hk_stocks

def test_hk_stocks_service():
    """测试港股股票列表服务"""
    print("测试港股股票列表服务...")
    
    result = get_hk_stocks()
    
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
    success = test_hk_stocks_service()
    sys.exit(0 if success else 1)
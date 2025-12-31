#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的akshare_hk模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.hk.akshare_hk import get_kline_data_from_akshare_hk
import json

def test_akshare_hk():
    """测试akshare_hk模块"""
    print("测试akshare_hk模块...")
    
    # 测试腾讯控股
    result = get_kline_data_from_akshare_hk(
        code='00700',
        formatted_code='0700.HK',
        market_type='HK',
        start_date='2024-01-01',
        end_date='2024-01-10'
    )
    
    print(f"结果类型: {type(result)}")
    
    if result:
        print(f"数据源: {result.get('data_source')}")
        data = result.get('data', [])
        print(f"数据长度: {len(data)}")
        
        if data:
            print("前3条数据:")
            for i, item in enumerate(data[:3]):
                print(f"  {i+1}. {item}")
        else:
            print("没有数据")
    else:
        print("没有返回结果")
    
    return result is not None

if __name__ == "__main__":
    success = test_akshare_hk()
    if success:
        print("\n测试成功!")
    else:
        print("\n测试失败!")
        sys.exit(1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试stock_hk_daily函数
"""

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import akshare as ak
    print("akshare导入成功")
except ImportError as e:
    print(f"akshare导入失败: {e}")
    sys.exit(1)

def test_stock_hk_daily():
    """测试stock_hk_daily函数"""
    print("测试stock_hk_daily函数...")
    
    try:
        # 调用stock_hk_daily
        data = ak.stock_hk_daily(
            symbol='00700',
            adjust='qfq'
        )
        
        print(f"返回数据类型: {type(data)}")
        if data is not None:
            print(f"数据形状: {data.shape}")
            print(f"列名: {list(data.columns)}")
            print(f"前几行数据:")
            print(data.head())
            
            # 检查date列
            if 'date' in data.columns:
                print(f"date列数据类型: {data['date'].dtype}")
                print(f"date列前几个值: {data['date'].head().tolist()}")
            else:
                print("没有date列，检查列名:")
                for col in data.columns:
                    print(f"  {col}: {data[col].dtype}")
        else:
            print("返回数据为None")
            
    except Exception as e:
        print(f"stock_hk_daily调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stock_hk_daily()
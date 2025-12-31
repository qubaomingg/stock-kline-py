#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试akshare_hk_daily函数调用失败问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import akshare as ak
import pandas as pd
from datetime import datetime

def test_stock_hk_daily():
    """测试stock_hk_daily函数"""
    try:
        print("测试stock_hk_daily函数...")
        
        # 测试代码
        code = "00700"
        
        print(f"调用ak.stock_hk_daily(symbol='{code}', adjust='qfq')...")
        data = ak.stock_hk_daily(symbol=code, adjust='qfq')
        
        if data is None:
            print("stock_hk_daily返回None")
            return False
        
        print(f"数据形状: {data.shape}")
        print(f"数据列名: {list(data.columns)}")
        print(f"数据类型: {type(data)}")
        
        if not data.empty:
            print("\n前5行数据:")
            print(data.head())
            print("\n后5行数据:")
            print(data.tail())
            
            # 检查date列
            if 'date' in data.columns:
                print(f"\ndate列数据类型: {data['date'].dtype}")
                print(f"date列前5个值: {data['date'].head().tolist()}")
            else:
                print(f"\n警告: 数据缺少date列，实际列名为: {list(data.columns)}")
                
                # 尝试找到日期列
                date_cols = [col for col in data.columns if 'date' in col.lower() or '日期' in col]
                if date_cols:
                    print(f"可能的日期列: {date_cols}")
                    data['date'] = data[date_cols[0]]
                    print(f"将{date_cols[0]}列重命名为date")
        
        return True
        
    except Exception as e:
        print(f"stock_hk_daily调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stock_hk_hist():
    """测试stock_hk_hist函数"""
    try:
        print("\n测试stock_hk_hist函数...")
        
        # 测试代码
        code = "00700"
        start_date = "20251201"
        end_date = "20251210"
        
        print(f"调用ak.stock_hk_hist(symbol='{code}', period='daily', start_date='{start_date}', end_date='{end_date}', adjust='qfq')...")
        data = ak.stock_hk_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date, adjust='qfq')
        
        if data is None:
            print("stock_hk_hist返回None")
            return False
        
        print(f"数据形状: {data.shape}")
        print(f"数据列名: {list(data.columns)}")
        
        if not data.empty:
            print("\n前5行数据:")
            print(data.head())
            
            # 检查日期列
            if '日期' in data.columns:
                print(f"\n日期列数据类型: {data['日期'].dtype}")
                print(f"日期列前5个值: {data['日期'].head().tolist()}")
        
        return True
        
    except Exception as e:
        print(f"stock_hk_hist调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始调试akshare_hk_daily函数调用失败问题...")
    print("=" * 60)
    
    success1 = test_stock_hk_daily()
    success2 = test_stock_hk_hist()
    
    print("=" * 60)
    print(f"测试结果: stock_hk_daily={'成功' if success1 else '失败'}, stock_hk_hist={'成功' if success2 else '失败'}")
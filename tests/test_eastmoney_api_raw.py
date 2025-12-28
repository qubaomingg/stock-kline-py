#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试东方财富API原始返回数据
"""

import requests
import json
import pandas as pd

def test_eastmoney_api_raw():
    """测试东方财富API原始返回数据"""
    print("测试东方财富API原始返回数据...")
    
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1, "pz": 10000,  # 页码+每页数量（10000覆盖全量港股）
        "po": 1, "np": 1, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2, "invt": 2, "fid": "f3", "fs": "m:128+t:3,m:128+t:4",  # 港股主板+创业板
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"API响应状态: {response.status_code}")
        print(f"数据总条数: {data.get('data', {}).get('total', 0)}")
        print(f"实际返回条数: {len(data.get('data', {}).get('diff', []))}")
        
        # 查看数据结构
        if data.get('data', {}).get('diff'):
            df = pd.DataFrame(data["data"]["diff"])
            print(f"\nDataFrame形状: {df.shape}")
            print(f"列名: {list(df.columns)}")
            
            # 显示前5行
            print("\n前5行数据:")
            print(df.head().to_string())
            
            # 检查是否有分页信息
            print(f"\n分页信息:")
            print(f"  pn: {params['pn']}")
            print(f"  pz: {params['pz']}")
            print(f"  total: {data.get('data', {}).get('total', 0)}")
            
            # 如果实际返回少于总数，说明需要分页
            total = data.get('data', {}).get('total', 0)
            actual = len(data.get('data', {}).get('diff', []))
            if total > actual:
                print(f"\n⚠️ 注意: API返回{actual}条数据，但总数为{total}条")
                print(f"需要分页获取，每页最大数量可能有限制")
                
                # 计算需要多少页
                pages_needed = (total + params['pz'] - 1) // params['pz']
                print(f"需要{pages_needed}页来获取所有数据")
        
        return data
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

if __name__ == "__main__":
    test_eastmoney_api_raw()
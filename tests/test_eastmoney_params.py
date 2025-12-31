#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试东方财富API参数格式
"""

import requests
import json
from datetime import datetime

def test_eastmoney_api_params():
    """测试东方财富API的不同参数格式"""
    
    # 测试参数
    code = "00700"  # 腾讯控股
    start_date = "2024-01-01"
    end_date = "2024-01-10"
    
    # 测试用例
    test_cases = [
        {
            "name": "当前实现：时间戳格式（毫秒）",
            "beg": int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000),
            "end": int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        },
        {
            "name": "日期格式：YYYYMMDD",
            "beg": start_date.replace("-", ""),
            "end": end_date.replace("-", "")
        },
        {
            "name": "日期格式：YYYY-MM-DD",
            "beg": start_date,
            "end": end_date
        },
        {
            "name": "日期格式：YYYY/MM/DD",
            "beg": start_date.replace("-", "/"),
            "end": end_date.replace("-", "/")
        },
        {
            "name": "特殊值：0和20500101",
            "beg": "0",
            "end": "20500101"
        }
    ]
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    eastmoney_code = code.zfill(5)
    
    for test_case in test_cases:
        print(f"\n=== 测试用例：{test_case['name']} ===")
        print(f"beg参数: {test_case['beg']}")
        print(f"end参数: {test_case['end']}")
        
        params = {
            "secid": f"116.{eastmoney_code}",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": test_case["beg"],
            "end": test_case["end"],
            "lmt": "10000",
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            print(f"API响应状态: rc={data.get('rc')}, rt={data.get('rt')}")
            print(f"返回数据量: {len(data.get('data', {}).get('klines', []))}")
            
            # 如果有数据，显示前几条
            klines = data.get("data", {}).get("klines", [])
            if klines:
                print(f"第一条数据: {klines[0]}")
                print(f"最后一条数据: {klines[-1]}")
            
            # 显示API调用的完整URL
            print(f"API URL: {response.url}")
            
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    test_eastmoney_api_params()
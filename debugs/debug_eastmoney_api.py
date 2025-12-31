#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试eastmoney API响应
"""
import sys
import os
import requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_eastmoney_api(code, start_date, end_date):
    """调试东方财富API响应"""
    eastmoney_code = code.zfill(5)  # 港股代码补零到5位
    
    # 构建API URL
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
    # 计算开始和结束时间戳（毫秒）
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 转换为时间戳（毫秒）
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # API参数
    params = {
        "secid": f"116.{eastmoney_code}",  # 港股市场代码116
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",  # 日K线
        "fqt": "1",    # 前复权
        "beg": start_timestamp,
        "end": end_timestamp,
        "lmt": "10000",  # 最大数据量
    }
    
    print(f"API请求参数:")
    print(f"  secid: {params['secid']}")
    print(f"  beg: {params['beg']} ({start_date})")
    print(f"  end: {params['end']} ({end_date})")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nAPI响应:")
        print(f"  rc: {data.get('rc')}")
        print(f"  rt: {data.get('rt')}")
        
        if data.get("rc") == 0:
            data_info = data.get("data", {})
            print(f"  code: {data_info.get('code')}")
            print(f"  market: {data_info.get('market')}")
            print(f"  name: {data_info.get('name')}")
            print(f"  dktotal: {data_info.get('dktotal')}")  # 总数据条数
            print(f"  preKPrice: {data_info.get('preKPrice')}")
            
            klines = data_info.get("klines", [])
            print(f"  获取到 {len(klines)} 条K线数据")
            if klines:
                print(f"  第一条数据日期: {klines[0].split(',')[0]}")
                print(f"  最后一条数据日期: {klines[-1].split(',')[0]}")
                
                # 检查数据是否在请求范围内
                first_date = klines[0].split(',')[0]
                last_date = klines[-1].split(',')[0]
                
                if first_date >= start_date and last_date <= end_date:
                    print(f"  ✅ 数据在请求范围内")
                else:
                    print(f"  ⚠️  数据超出请求范围")
                    print(f"     请求: {start_date} 到 {end_date}")
                    print(f"     实际: {first_date} 到 {last_date}")
        else:
            print(f"  API错误: rc={data.get('rc')}, rt={data.get('rt')}")
            print(f"  完整响应: {data}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    print("=== 调试eastmoney API ===\n")
    
    # 测试不同的时间范围
    test_cases = [
        ("00700", "2024-01-01", "2024-01-10"),
        ("00700", "2024-01-01", "2024-01-31"),
        ("00700", "2023-12-01", "2024-01-31"),
        ("00700", "2024-01-15", "2024-01-20"),  # 更短的范围
        ("00700", "2024-01-01", "2024-02-01"),  # 跨月
    ]
    
    for code, start_date, end_date in test_cases:
        print(f"\n测试股票代码: {code}, 时间范围: {start_date} 到 {end_date}")
        print("-" * 50)
        debug_eastmoney_api(code, start_date, end_date)
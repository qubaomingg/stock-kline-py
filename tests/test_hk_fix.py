#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的akshare_hk时间参数
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.hk.akshare_hk import get_kline_data_from_akshare_hk

# 测试腾讯控股 (00700.HK)
test_cases = [
    {
        "name": "腾讯控股 - 短期范围",
        "code": "00700",
        "formatted_code": "0700.HK",
        "market_type": "HK",
        "start_date": "2025-12-01",
        "end_date": "2025-12-10"
    },
    {
        "name": "腾讯控股 - 长期范围",
        "code": "00700",
        "formatted_code": "0700.HK",
        "market_type": "HK",
        "start_date": "2025-10-01",
        "end_date": "2025-12-20"
    }
]

print("测试akshare_hk时间参数修复...")
print("=" * 50)

for test_case in test_cases:
    print(f"\n测试: {test_case['name']}")
    print(f"代码: {test_case['code']} ({test_case['formatted_code']})")
    print(f"时间范围: {test_case['start_date']} 到 {test_case['end_date']}")
    
    result = get_kline_data_from_akshare_hk(
        code=test_case['code'],
        formatted_code=test_case['formatted_code'],
        market_type=test_case['market_type'],
        start_date=test_case['start_date'],
        end_date=test_case['end_date']
    )
    
    if result:
        data = result.get("data", [])
        data_source = result.get("data_source", "unknown")
        print(f"✓ 数据源: {data_source}")
        print(f"✓ 获取数据条数: {len(data)}")
        
        if data:
            # 显示前3条和后3条数据
            print(f"✓ 数据日期范围:")
            for i, item in enumerate(data[:3]):
                print(f"  前{i+1}: {item['date']} - 收盘价: {item['close']}")
            
            if len(data) > 6:
                print(f"  ... (中间省略 {len(data)-6} 条数据)")
                
            for i, item in enumerate(data[-3:], 1):
                print(f"  后{i}: {item['date']} - 收盘价: {item['close']}")
            
            # 检查时间参数是否生效
            first_date = data[0]['date']
            last_date = data[-1]['date']
            
            if first_date >= test_case['start_date'] and last_date <= test_case['end_date']:
                print(f"✓ 时间参数生效: 数据在请求范围内 ({first_date} 到 {last_date})")
            else:
                print(f"✗ 时间参数可能未生效: 数据超出请求范围")
                print(f"  请求范围: {test_case['start_date']} 到 {test_case['end_date']}")
                print(f"  实际范围: {first_date} 到 {last_date}")
        else:
            print("✗ 获取到空数据")
    else:
        print("✗ 获取数据失败")
    
    print("-" * 50)

print("\n测试完成！")
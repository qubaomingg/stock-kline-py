#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化后的yfinance模块
"""

import sys
sys.path.append('.')

from service.kline.us.yfinance import get_kline_data_from_yfinance

print("测试简化后的yfinance模块...")

result = get_kline_data_from_yfinance(
    code='TSLA',
    formatted_code='TSLA',
    market_type='US',
    start_date='2024-12-01',
    end_date='2024-12-10'
)

print(f"测试结果: {'成功' if result else '失败'}")
if result:
    print(f"数据源: {result['data_source']}")
    print(f"数据条数: {len(result['data'])}")
    print(f"第一条数据: {result['data'][0] if result['data'] else '空'}")
else:
    print("yfinance数据源失败，这是正常的，因为存在速率限制")
    print("系统应该会自动切换到其他数据源")

# 测试主kline服务的数据源切换
print("\n测试主kline服务的数据源切换...")
try:
    from service.kline.kline import get_kline_data
    
    # 测试美股
    print("测试美股TSLA:")
    kline_result = get_kline_data(
        code='TSLA',
        start_date='2024-12-01',
        end_date='2024-12-10'
    )
    
    if kline_result:
        print(f"最终使用的数据源: {kline_result['data_source']}")
        print(f"数据条数: {len(kline_result['data'])}")
    else:
        print("所有数据源都失败了")
        
except Exception as e:
    print(f"测试主服务时出错: {e}")
    import traceback
    traceback.print_exc()
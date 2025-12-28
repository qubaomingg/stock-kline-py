#!/usr/bin/env python3
"""
测试 Intrinio 数据源的 search 功能
"""

import sys
import os
sys.path.append('.')

from openbb import obb

print("测试 Intrinio 数据源的 search 功能...")

# 测试 search 功能
print("\n1. 测试空查询获取所有股票:")
try:
    result = obb.equity.search(
        query="",  # 空查询获取所有股票
        provider="intrinio",
        use_cache=True
    )
    
    if result is None:
        print("  result 为 None")
    elif result.results is None:
        print("  result.results 为 None")
    else:
        df = result.results
        print(f"  成功获取到 {len(df)} 条记录")
        if len(df) > 0:
            print("  前5条记录:")
            print(df.head())
            
            # 检查列名
            print("\n  列名:")
            print(list(df.columns))
            
            # 检查是否有交易所信息
            if 'exchange' in df.columns:
                print("\n  交易所分布:")
                print(df['exchange'].value_counts().head())
            
            # 检查是否有市值信息
            if 'market_cap' in df.columns:
                print("\n  市值信息示例:")
                print(df[['symbol', 'name', 'market_cap']].head())
        
except Exception as e:
    print(f"  发生错误: {e}")
    import traceback
    traceback.print_exc()

print("\n2. 测试查询特定股票:")
try:
    result = obb.equity.search(
        query="AAPL",
        provider="intrinio",
        use_cache=True
    )
    
    if result is None:
        print("  result 为 None")
    elif result.results is None:
        print("  result.results 为 None")
    else:
        df = result.results
        print(f"  成功获取到 {len(df)} 条记录")
        if len(df) > 0:
            print("  查询结果:")
            print(df)
        
except Exception as e:
    print(f"  发生错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成!")
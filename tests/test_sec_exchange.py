#!/usr/bin/env python3
"""
测试 SEC 数据源的 exchange 参数格式
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openbb import obb
import pandas as pd

print("测试 SEC 数据源的 exchange 参数格式")
print("=" * 50)

# 测试不同的 exchange 参数值
exchange_tests = [
    "N",  # 当前代码使用的
    "A",
    "P",
    "nasdaq",
    "nyse",
    "amex",
    "NASDAQ",
    "NYSE",
    "AMEX",
    "nas",
    "nyq",
]

# 先获取一次所有数据作为基准
print("\n获取基准数据（无exchange参数）:")
try:
    result = obb.equity.search(
        is_fund=False,
        provider="sec"
    )
    
    if hasattr(result, 'to_df'):
        df_all = result.to_df()
        print(f"  成功获取到 {len(df_all)} 条记录")
        if not df_all.empty:
            print(f"  示例: {df_all.iloc[0]['symbol']} - {df_all.iloc[0]['name']}")
            # 检查是否有exchange列
            if 'exchange' in df_all.columns:
                print(f"  数据包含exchange列，唯一值: {df_all['exchange'].unique()[:10]}")
            else:
                print(f"  数据不包含exchange列，列名: {df_all.columns.tolist()}")
    else:
        print(f"  返回结果类型: {type(result)}")
        print(f"  结果: {result}")
except Exception as e:
    print(f"  错误: {e}")

print("\n" + "=" * 50)
print("测试不同exchange参数:")

for exchange in exchange_tests:
    print(f"\n测试 exchange='{exchange}':")
    try:
        result = obb.equity.search(
            exchange=exchange,
            is_fund=False,
            provider="sec"
        )
        
        if hasattr(result, 'to_df'):
            df = result.to_df()
            print(f"  成功获取到 {len(df)} 条记录")
            if not df.empty:
                print(f"  示例: {df.iloc[0]['symbol']} - {df.iloc[0]['name']}")
                # 检查是否有exchange列
                if 'exchange' in df.columns:
                    exchange_counts = df['exchange'].value_counts().head(5)
                    print(f"  交易所分布（前5）: {dict(exchange_counts)}")
                else:
                    print(f"  数据不包含exchange列")
                
                # 检查与基准数据的差异
                if 'df_all' in locals() and not df_all.empty:
                    if len(df) == len(df_all):
                        print(f"  注意: 返回记录数与基准相同，exchange参数可能被忽略")
        else:
            print(f"  返回结果类型: {type(result)}")
            print(f"  结果: {result}")
    except Exception as e:
        print(f"  错误: {e}")

print("\n测试完成")
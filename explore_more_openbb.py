#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入探索 openbb 的港股数据
"""
from openbb import obb
import pandas as pd

print("=" * 70)
print("深入探索 openbb 的港股数据源")
print("=" * 70)

print("\n", "-" * 70)
print("1. 查看 obb.equity 的所有可用方法")
print("-" * 70)
eq_attrs = dir(obb.equity)
print("共", len(eq_attrs), "个属性/方法")
for attr in eq_attrs:
    print("  -", attr)

print("\n", "-" * 70)
print("2. 尝试 obb.equity.screener")
print("-" * 70)
try:
    # 尝试筛选港股
    print("尝试筛选港股市场:")
    try:
        result = obb.equity.screener()
        if hasattr(result, 'to_df'):
            df = result.to_df()
            print("成功！获取到", len(df), "只股票")
            print("\n列名:", df.columns.tolist()[:30])
            print("\n前 5 只:")
            print(df.head())
    except Exception as e:
        print("尝试失败:", e)
except Exception as e:
    print("screener 失败:", e)

print("\n", "-" * 70)
print("3. 尝试 obb.equity.search 更多参数")
print("-" * 70)
keywords = ['Tencent', 'Alibaba', 'Hong Kong', 'HK', '00700', '00001']
for word in keywords:
    try:
        result = obb.equity.search(query=word)
        if hasattr(result, 'to_df'):
            df = result.to_df()
            if len(df) > 0:
                print(f"\n✓ 搜索 '{word}' 找到 {len(df)} 条结果")
                print("列名:", df.columns.tolist())
                print(df.head())
    except Exception as e:
        print(f"搜索 '{word}' 失败:", e)

print("\n", "-" * 70)
print("4. 查看 openbb 的 providers")
print("-" * 70)
try:
    print(dir(obb.system))
except Exception as e:
    print("查看 providers 失败:", e)

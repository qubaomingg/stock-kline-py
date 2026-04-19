#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索 openbb 的 screener、discovery、reference 等模块
"""

from openbb import obb

print("=" * 70)
print("探索 openbb 的 screener、discovery、reference 模块")
print("=" * 70)

print("\n" + "=" * 70)
print("1. 探索 obb.reference（可能有市场/交易所列表）")
print("=" * 70)
try:
    print("obb.reference 的属性:", [attr for attr in dir(obb.reference) if not attr.startswith('_')])
except Exception as e:
    print(f"❌ 查看 obb.reference 失败: {e}")

print("\n" + "=" * 70)
print("2. 探索 obb.equity.discovery")
print("=" * 70)
try:
    print("obb.equity.discovery 的属性:", [attr for attr in dir(obb.equity.discovery) if not attr.startswith('_')])
except Exception as e:
    print(f"❌ 查看 obb.equity.discovery 失败: {e}")

print("\n" + "=" * 70)
print("3. 探索 obb.equity.screener")
print("=" * 70)
try:
    print("尝试查看 obb.equity.screener 的用法:")
    if hasattr(obb.equity, 'screener') and callable(obb.equity.screener):
        print("screener 是可调用的!")
except Exception as e:
    print(f"❌ 查看 obb.equity.screener 失败: {e}")

print("\n" + "=" * 70)
print("4. 直接尝试用 akshare 获取更多港股数据")
print("=" * 70)
import akshare as ak
print("搜索 akshare 中包含 'hk' 的函数:")
hk_functions = [func for func in dir(ak) if 'hk' in func.lower()]
print(f"找到 {len(hk_functions)} 个包含 hk 的函数:", hk_functions[:50])

print("\n" + "=" * 70)
print("5. 尝试几个 akshare 港股相关函数")
print("=" * 70)
functions_to_test = [
    "stock_hk_spot",
    "stock_hk_spot_em",
    "stock_hk_sse_summary",
    "stock_hk_sse_component",
    "stock_hk_sse_component_em",
    "stock_hk_index_cninfo",
    "stock_hk_ggt_ss_em",
    "stock_hk_hsgt_em",
]
for func_name in functions_to_test:
    try:
        if hasattr(ak, func_name):
            func = getattr(ak, func_name)
            print(f"\n尝试 {func_name}:")
            try:
                result = func()
                if hasattr(result, 'empty') and not result.empty:
                    print(f"✅ {func_name} 成功，共 {len(result)} 行")
                    print(result.head(5))
            except Exception as e:
                print(f"❌ 执行失败: {e}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")

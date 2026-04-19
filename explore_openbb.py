#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索 openbb 支持的港股数据渠道
"""

import sys
import os

print("=" * 70)
print("探索 openbb 港股数据渠道")
print("=" * 70)

try:
    from openbb import obb
    print("✅ 成功导入 openbb")
    
    print("\n" + "=" * 70)
    print("1. 查看 obb 的属性和方法")
    print("=" * 70)
    print("obb 的主要属性:", [attr for attr in dir(obb) if not attr.startswith('_')][:50])
    
    print("\n" + "=" * 70)
    print("2. 查看 obb.equity 的属性和方法")
    print("=" * 70)
    equity_attrs = [attr for attr in dir(obb.equity) if not attr.startswith('_')]
    print("obb.equity 的主要属性:", equity_attrs)
    
    print("\n" + "=" * 70)
    print("3. 查找可能包含 hk、hong kong、stock、symbol、list 的属性")
    print("=" * 70)
    for attr in equity_attrs:
        lower_attr = attr.lower()
        if any(keyword in lower_attr for keyword in ['hk', 'hong', 'stock', 'symbol', 'list', 'screener', 'search', 'market', 'equity']):
            print(f"  ✅ 可能相关: {attr}")
    
    print("\n" + "=" * 70)
    print("4. 尝试搜索港股的一些关键词")
    print("=" * 70)
    try:
        print("\n尝试搜索 '00700'（腾讯）:")
        result = obb.equity.search('00700')
        print(result)
        if hasattr(result, 'to_df') and not result.to_df().empty:
            print(f"✅ 找到数据，共 {len(result.to_df())} 条")
            print(result.to_df())
    except Exception as e:
        print(f"❌ 搜索 00700 失败: {e}")
    
    try:
        print("\n尝试搜索 'tencent':")
        result = obb.equity.search('tencent')
        print(result)
        if hasattr(result, 'to_df') and not result.to_df().empty:
            print(f"✅ 找到数据，共 {len(result.to_df())} 条")
            print(result.to_df())
    except Exception as e:
        print(f"❌ 搜索 tencent 失败: {e}")
    
    print("\n" + "=" * 70)
    print("5. 尝试查看其他可能的数据源")
    print("=" * 70)
    try:
        if hasattr(obb, 'index'):
            print("\n尝试 obb.index:")
            print(dir(obb.index))
    except Exception as e:
        print(f"❌ 查看 obb.index 失败: {e}")
    
    try:
        if hasattr(obb, 'etf'):
            print("\n尝试 obb.etf:")
            print(dir(obb.etf))
    except Exception as e:
        print(f"❌ 查看 obb.etf 失败: {e}")
    
    print("\n" + "=" * 70)
    print("6. 查看 obb.equity 的所有可能方法")
    print("=" * 70)
    for attr in dir(obb.equity):
        if not attr.startswith('_'):
            try:
                value = getattr(obb.equity, attr)
                if callable(value):
                    print(f"  可调用: {attr}")
                else:
                    print(f"  属性: {attr}")
            except Exception:
                pass
                
except Exception as e:
    print(f"❌ 导入 openbb 失败: {e}")
    import traceback
    traceback.print_exc()

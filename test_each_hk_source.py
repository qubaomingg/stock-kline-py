#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试每个港股数据源能获取多少只股票
"""
import sys
import os

# 路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from service.stocks.hk.extended_hk_stocks import get_hk_stocks_by_extended
from service.stocks.hk.finnhub_stocks import get_hk_stocks_by_finnhub
from service.stocks.hk.openbb_stocks import get_hk_stocks_by_openbb
from service.stocks.hk.ak_stocks import get_hk_stocks_by_ak
from service.stocks.hk.eastmoney_stocks import get_hk_stocks_by_eastmoney

print("=" * 70)
print("测试每个港股数据源能获取多少只股票")
print("=" * 70)

results = []

# 测试 extended_hk_stocks
print(f"\n{'=' * 70}")
print("数据源: extended_hk_stocks")
print('=' * 70)
try:
    result = get_hk_stocks_by_extended()
    if result and result.get('stocks'):
        count = len(result['stocks'])
        print(f"✓ 成功! 股票数量: {count}")
        results.append(('extended_hk_stocks', count, '成功'))
    else:
        print("✗ 无数据返回")
        results.append(('extended_hk_stocks', 0, '无数据返回'))
except Exception as e:
    print(f"✗ 异常: {e}")
    results.append(('extended_hk_stocks', 0, f'异常'))

# 测试 finnhub_stocks
print(f"\n{'=' * 70}")
print("数据源: finnhub_stocks")
print('=' * 70)
try:
    result = get_hk_stocks_by_finnhub()
    if result and result.get('stocks'):
        count = len(result['stocks'])
        print(f"✓ 成功! 股票数量: {count}")
        results.append(('finnhub_stocks', count, '成功'))
    else:
        print("✗ 无数据返回")
        results.append(('finnhub_stocks', 0, '无数据返回'))
except Exception as e:
    print(f"✗ 异常: {e}")
    results.append(('finnhub_stocks', 0, f'异常'))

# 测试 openbb_stocks
print(f"\n{'=' * 70}")
print("数据源: openbb_stocks")
print('=' * 70)
try:
    result = get_hk_stocks_by_openbb()
    if result and result.get('stocks'):
        count = len(result['stocks'])
        print(f"✓ 成功! 股票数量: {count}")
        results.append(('openbb_stocks', count, '成功'))
    else:
        print("✗ 无数据返回")
        results.append(('openbb_stocks', 0, '无数据返回'))
except Exception as e:
    print(f"✗ 异常: {e}")
    results.append(('openbb_stocks', 0, f'异常'))

# 测试 ak_stocks
print(f"\n{'=' * 70}")
print("数据源: ak_stocks")
print('=' * 70)
try:
    result = get_hk_stocks_by_ak()
    if result and result.get('stocks'):
        count = len(result['stocks'])
        print(f"✓ 成功! 股票数量: {count}")
        results.append(('ak_stocks', count, '成功'))
    else:
        print("✗ 无数据返回")
        results.append(('ak_stocks', 0, '无数据返回'))
except Exception as e:
    print(f"✗ 异常: {e}")
    results.append(('ak_stocks', 0, f'异常'))

# 测试 eastmoney_stocks
print(f"\n{'=' * 70}")
print("数据源: eastmoney_stocks")
print('=' * 70)
try:
    result = get_hk_stocks_by_eastmoney()
    if result and result.get('stocks'):
        count = len(result['stocks'])
        print(f"✓ 成功! 股票数量: {count}")
        results.append(('eastmoney_stocks', count, '成功'))
    else:
        print("✗ 无数据返回")
        results.append(('eastmoney_stocks', 0, '无数据返回'))
except Exception as e:
    print(f"✗ 异常: {e}")
    results.append(('eastmoney_stocks', 0, f'异常'))

# 汇总
print(f"\n{'=' * 70}")
print("汇总结果")
print('=' * 70)
for name, count, status in results:
    print(f"{name:20} | {count:6} 只 | {status}")

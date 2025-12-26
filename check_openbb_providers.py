#!/usr/bin/env python3
"""
检查OpenBB支持的提供商
"""

import os
import sys
from dotenv import load_dotenv
from openbb import obb

# 加载环境变量
load_dotenv()

print("检查OpenBB提供商支持情况")
print("=" * 50)

# 检查所有提供商
print("\n1. 列出所有提供商:")
try:
    providers = obb.coverage.providers
    if providers:
        print(f"共有 {len(providers)} 个提供商:")
        for i, provider in enumerate(providers, 1):
            provider_name = provider.name if hasattr(provider, 'name') else str(provider)
            print(f"  {i}. {provider_name}")
    else:
        print("无法获取提供商列表")
except Exception as e:
    print(f"错误: {e}")

print("\n2. 检查equity.screener支持的提供商:")
try:
    # 获取equity.screener的提供商信息
    screener_providers = obb.coverage.command("equity.screener")
    if screener_providers:
        print(f"equity.screener支持的提供商:")
        for provider in screener_providers:
            print(f"  - {provider}")
    else:
        print("无法获取equity.screener的提供商信息")
except Exception as e:
    print(f"错误: {e}")

print("\n3. 检查equity.search支持的提供商:")
try:
    # 获取equity.search的提供商信息
    search_providers = obb.coverage.command("equity.search")
    if search_providers:
        print(f"equity.search支持的提供商:")
        for provider in search_providers:
            print(f"  - {provider}")
    else:
        print("无法获取equity.search的提供商信息")
except Exception as e:
    print(f"错误: {e}")

print("\n4. 检查可用的股票数据提供商:")
try:
    # 尝试查找可用的股票数据提供商
    available_providers = []
    
    # 检查一些常见的提供商
    test_providers = ["yfinance", "polygon", "alpha_vantage", "tiingo", "fmp", "intrinio", "sec"]
    
    for provider_name in test_providers:
        try:
            # 尝试调用一个简单的函数
            result = obb.equity.search(
                provider=provider_name,
                query="AAPL"
            )
            if result is not None:
                available_providers.append(provider_name)
                print(f"  ✓ {provider_name}: 可用")
            else:
                print(f"  ✗ {provider_name}: 不可用")
        except Exception as e:
            print(f"  ✗ {provider_name}: 错误 - {str(e)[:100]}")
    
    print(f"\n可用的股票数据提供商: {available_providers}")
except Exception as e:
    print(f"错误: {e}")

print("\n5. 检查exchange参数的有效值:")
try:
    # 从错误信息中提取有效的exchange值
    valid_exchanges = [
        'amex', 'ams', 'ase', 'asx', 'ath', 'bme', 'bru', 'bud', 'bue', 'cai',
        'cnq', 'cph', 'dfm', 'doh', 'etf', 'euronext', 'hel', 'hkse', 'ice',
        'iob', 'ist', 'jkt', 'jnb', 'jpx', 'kls', 'koe', 'ksc', 'kuw', 'lse',
        'mex', 'mutual_fund', 'nasdaq', 'neo', 'nse', 'nyse', 'nze', 'osl',
        'otc', 'pnk', 'pra', 'ris', 'sao', 'sau', 'set', 'sgo', 'shh', 'shz',
        'six', 'sto', 'tai', 'tlv', 'tsx', 'two', 'vie', 'wse', 'xetra'
    ]
    
    print(f"有效的exchange值 ({len(valid_exchanges)}个):")
    for i, exchange in enumerate(valid_exchanges, 1):
        print(f"  {exchange}", end=" ")
        if i % 5 == 0:
            print()
    print()
except Exception as e:
    print(f"错误: {e}")

print("\n检查完成")
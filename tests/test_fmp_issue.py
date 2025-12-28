#!/usr/bin/env python3
"""
测试FMP数据源问题
"""

import os
import sys
from dotenv import load_dotenv
from openbb import obb

# 加载环境变量
load_dotenv()

# 设置FMP API密钥
fmp_api_key = os.getenv("FMP_API_KEY")
if not fmp_api_key:
    print("错误: 未找到 FMP_API_KEY 环境变量")
    sys.exit(1)

print(f"FMP API密钥已设置: {fmp_api_key[:10]}...")

# 设置OpenBB的FMP凭证
obb.user.credentials.fmp_api_key = fmp_api_key

# 测试不同的API调用方式
print("\n测试1: 使用equity.screener方法")
try:
    result = obb.equity.screener(
        provider="fmp",
        exchange="nyq",
        type="stock"
    )
    print(f"结果类型: {type(result)}")
    if result:
        print(f"是否为空: {result.empty if hasattr(result, 'empty') else 'N/A'}")
        if hasattr(result, 'results') and result.results is not None:
            print(f"结果数量: {len(result.results) if not result.results.empty else 0}")
            if not result.results.empty:
                print(f"前几列: {list(result.results.columns[:5])}")
    else:
        print("结果为None")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试2: 使用equity.search方法")
try:
    result = obb.equity.search(
        provider="fmp",
        query="",
        exchange="nyq",
        type="stock"
    )
    print(f"结果类型: {type(result)}")
    if result:
        print(f"是否为空: {result.empty if hasattr(result, 'empty') else 'N/A'}")
        if hasattr(result, 'results') and result.results is not None:
            print(f"结果数量: {len(result.results) if not result.results.empty else 0}")
            if not result.results.empty:
                print(f"前几列: {list(result.results.columns[:5])}")
    else:
        print("结果为None")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试3: 检查FMP提供商支持的功能")
try:
    # 检查FMP提供商
    from openbb_core.provider.abstract.provider import Provider
    providers = obb.coverage.providers
    print(f"可用提供商数量: {len(providers) if providers else 0}")
    
    # 查找FMP提供商
    fmp_provider = None
    for provider in providers:
        if hasattr(provider, 'name') and provider.name == 'fmp':
            fmp_provider = provider
            break
    
    if fmp_provider:
        print(f"找到FMP提供商: {fmp_provider}")
        if hasattr(fmp_provider, 'description'):
            print(f"描述: {fmp_provider.description}")
    else:
        print("未找到FMP提供商")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成")
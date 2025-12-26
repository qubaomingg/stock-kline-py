#!/usr/bin/env python3
"""
直接测试OpenBB的FMP调用
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from openbb import obb

print("直接测试OpenBB的FMP调用")
print("=" * 50)

# 检查API密钥
fmp_api_key = os.getenv("FMP_API_KEY")
if not fmp_api_key:
    print("错误: 未找到 FMP_API_KEY 环境变量")
    print("请检查 .env 文件")
    sys.exit(1)
else:
    print(f"✓ 找到 FMP_API_KEY: {fmp_api_key[:10]}...")

# 设置凭证
obb.user.credentials.fmp_api_key = fmp_api_key
print("✓ 已设置FMP凭证")

# 测试equity.screener
print("\n1. 测试 equity.screener (provider='fmp', exchange='nyse', type='stock'):")
try:
    result = obb.equity.screener(
        provider="fmp",
        exchange="nyse",
        type="stock"
    )
    print(f"✓ 调用成功")
    if result:
        print(f"  - 结果类型: {type(result)}")
        if hasattr(result, 'results'):
            print(f"  - results类型: {type(result.results)}")
            if result.results is not None:
                print(f"  - 数据行数: {len(result.results)}")
                if not result.results.empty:
                    print(f"  - 列名: {list(result.results.columns)}")
                    print(f"  - 前5行:")
                    print(result.results.head())
                else:
                    print("  - 数据为空")
            else:
                print("  - results为None")
        else:
            print(f"  - 结果属性: {dir(result)}")
    else:
        print("  - 结果为None")
except Exception as e:
    print(f"✗ 调用失败: {e}")
    import traceback
    traceback.print_exc()

# 测试其他exchange
print("\n2. 测试其他exchange:")
for exchange in ["nasdaq", "amex"]:
    print(f"\n  测试 exchange='{exchange}':")
    try:
        result = obb.equity.screener(
            provider="fmp",
            exchange=exchange,
            type="stock"
        )
        print(f"  ✓ 调用成功")
        if result and hasattr(result, 'results') and result.results is not None:
            print(f"    数据行数: {len(result.results)}")
        else:
            print(f"    无数据")
    except Exception as e:
        print(f"  ✗ 调用失败: {e}")

print("\n测试完成")
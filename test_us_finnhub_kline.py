#!/usr/bin/env python3
"""
测试 US 市场 Finnhub K 线数据获取
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print("已加载 .env 文件中的环境变量")

from service.kline.us.finnhub import get_kline_data_from_finnhub, is_finnhub_available
from service.kline.kline import get_kline_data


def test_finnhub_direct():
    """直接测试 Finnhub 模块"""
    print("=" * 60)
    print("直接测试 Finnhub 模块")
    print("=" * 60)

    print(f"\nfinnhub 库可用: {is_finnhub_available()}")

    api_key = os.getenv('FINNHUB_API_KEY', '')
    print(f"FINNHUB_API_KEY 已设置: {bool(api_key)}")

    if not api_key:
        print("未设置 FINNHUB_API_KEY，跳过测试")
        return False

    # 测试获取 AAPL 数据
    print("\n测试获取 AAPL 数据...")
    result = get_kline_data_from_finnhub(
        code="AAPL",
        formatted_code="AAPL",
        market_type="us",
        start_date="2024-01-01",
        end_date="2024-01-20",
        api_key=api_key
    )

    if result:
        print(f"✓ 成功获取数据: {result['data_source']}, 数据条数: {len(result['data'])}")
        if result['data']:
            print("\n前3条数据:")
            for item in result['data'][:3]:
                print(f"  {item['date']}: O={item['open']}, H={item['high']}, L={item['low']}, C={item['close']}, V={item.get('volume', 0)}")
        return True
    else:
        print("✗ 获取数据失败")
        return False


def test_finnhub_via_kline_service():
    """通过 kline 服务测试 Finnhub"""
    print("\n" + "=" * 60)
    print("通过 kline 服务测试 Finnhub")
    print("=" * 60)

    # 测试只使用 Finnhub 数据源
    print("\n测试只使用 Finnhub 数据源获取 AAPL 数据...")
    result = get_kline_data(
        code="AAPL",
        start_date="2024-01-01",
        end_date="2024-01-20",
        data_sources=["finnhub"]
    )

    if result and result.get('data'):
        print(f"✓ 成功获取数据，使用数据源: {result.get('data_source')}")
        print(f"  数据条数: {len(result['data'])}")
        if result['data']:
            print("\n前3条数据:")
            for item in result['data'][:3]:
                print(f"  {item['date']}: O={item['open']}, H={item['high']}, L={item['low']}, C={item['close']}")
        return True
    else:
        print(f"✗ 获取数据失败: {result.get('error', '未知错误')}")
        return False


def test_multiple_stocks():
    """测试多个股票"""
    print("\n" + "=" * 60)
    print("测试多个股票")
    print("=" * 60)

    test_codes = ["AAPL", "TSLA", "NVDA", "MSFT"]
    results = {}

    for code in test_codes:
        print(f"\n测试 {code}...")
        try:
            result = get_kline_data(
                code=code,
                start_date="2024-01-01",
                end_date="2024-01-10",
                data_sources=["finnhub"]
            )
            if result and result.get('data'):
                print(f"✓ {code} 成功，数据条数: {len(result['data'])}")
                results[code] = True
            else:
                print(f"✗ {code} 失败")
                results[code] = False
        except Exception as e:
            print(f"✗ {code} 异常: {e}")
            results[code] = False

    return all(results.values())


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("US 市场 Finnhub K 线数据测试")
    print("=" * 60)

    all_passed = True

    # 测试1: 直接测试 Finnhub 模块
    if not test_finnhub_direct():
        all_passed = False

    # 测试2: 通过 kline 服务测试
    if not test_finnhub_via_kline_service():
        all_passed = False

    # 测试3: 测试多个股票
    if not test_multiple_stocks():
        all_passed = False

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总体: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
测试美国股票市场股票列表的所有支持来源
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
else:
    print("未找到 .env 文件")

from service.stocks.us.us_stocks import get_us_stocks
from service.stocks.us.sec_stocks import get_sec_stocks_all, get_sec_stocks
from service.stocks.us.finnhub_stocks import get_finnhub_stocks_all, get_finnhub_stocks


def test_sec_source():
    """测试 SEC 数据源"""
    print("=" * 60)
    print("测试 SEC 数据源")
    print("=" * 60)
    
    try:
        # 测试单个交易所
        print("\n1. 测试 Nasdaq 交易所:")
        result = get_sec_stocks("N")
        if result:
            print(f"✓ 成功获取到 {result['count']} 只股票")
            if result['stocks']:
                print("  前3只股票:")
                for stock in result['stocks'][:3]:
                    print(f"    {stock['code']}: {stock['name']}")
        else:
            print("✗ 获取失败")
        
        # 测试所有交易所
        print("\n2. 测试所有交易所 (合并):")
        result = get_sec_stocks_all()
        if result:
            print(f"✓ 成功获取到 {result['count']} 只唯一股票")
            print(f"  数据源: {result.get('source', 'unknown')}")
            if result['stocks']:
                print("  前3只股票:")
                for stock in result['stocks'][:3]:
                    print(f"    {stock['code']}: {stock['name']}")
            return True
        else:
            print("✗ 获取失败")
            return False
            
    except Exception as e:
        print(f"✗ SEC 数据源测试出错: {e}")
        return False


def test_finnhub_source():
    """测试 Finnhub 数据源"""
    print("\n" + "=" * 60)
    print("测试 Finnhub 数据源")
    print("=" * 60)
    
    try:
        # 检查 API Key
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key or api_key == "YOUR_FINNHUB_API_KEY":
            print("⚠ 警告: FINNHUB_API_KEY 未设置，Finnhub 数据源可能无法正常工作")
            print("  设置方式: export FINNHUB_API_KEY='your_api_key'")
        
        # 测试单个交易所
        print("\n1. 测试 US 交易所:")
        result = get_finnhub_stocks("US")
        if result:
            print(f"✓ 成功获取到 {result['count']} 只股票")
            if result['stocks']:
                print("  前3只股票:")
                for stock in result['stocks'][:3]:
                    print(f"    {stock['code']}: {stock['name']}")
        else:
            print("✗ 获取失败")
        
        # 测试所有交易所
        print("\n2. 测试所有交易所:")
        result = get_finnhub_stocks_all()
        if result:
            print(f"✓ 成功获取到 {result['count']} 只唯一股票")
            print(f"  数据源: {result.get('source', 'unknown')}")
            if result['stocks']:
                print("  前3只股票:")
                for stock in result['stocks'][:3]:
                    print(f"    {stock['code']}: {stock['name']}")
            return True
        else:
            print("✗ 获取失败")
            return False
            
    except Exception as e:
        print(f"✗ Finnhub 数据源测试出错: {e}")
        return False


def test_priority_fallback():
    """测试优先级和兜底机制"""
    print("\n" + "=" * 60)
    print("测试优先级和兜底机制")
    print("=" * 60)
    
    try:
        print("\n1. 测试按优先级获取（不指定数据源）:")
        result = get_us_stocks()
        if result:
            print(f"✓ 成功获取到 {result['count']} 只股票")
            print(f"  使用的数据源: {result.get('source', 'unknown')}")
            if result['stocks']:
                print("  前3只股票:")
                for stock in result['stocks'][:3]:
                    print(f"    {stock['code']}: {stock['name']}")
            return True
        else:
            print("✗ 获取失败")
            return False
            
    except Exception as e:
        print(f"✗ 优先级测试出错: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("美国股票市场股票列表数据源测试")
    print("=" * 60)
    
    results = {}
    
    # 测试 SEC 数据源
    results['sec'] = test_sec_source()
    
    # 测试 Finnhub 数据源
    results['finnhub'] = test_finnhub_source()
    
    # 测试优先级和兜底
    results['fallback'] = test_priority_fallback()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"SEC 数据源: {'✓ 通过' if results['sec'] else '✗ 失败'}")
    print(f"Finnhub 数据源: {'✓ 通过' if results['finnhub'] else '✗ 失败'}")
    print(f"优先级/兜底机制: {'✓ 通过' if results['fallback'] else '✗ 失败'}")
    
    all_passed = all(results.values())
    print(f"\n总体: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

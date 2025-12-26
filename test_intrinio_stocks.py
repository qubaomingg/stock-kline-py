#!/usr/bin/env python3
"""
测试 Intrinio 数据源美股列表查询功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.stocks.us.intrinio_stocks import get_intrinio_stocks, get_intrinio_stocks_all


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    # 测试单个交易所
    print("\n1. 测试 Nasdaq 交易所:")
    result = get_intrinio_stocks("nasdaq")
    if result:
        print(f"   获取到 {result['count']} 只股票")
        if result["stocks"]:
            print("   前5只股票:")
            for stock in result["stocks"][:5]:
                print(f"     {stock['code']}: {stock['name']} (市值: {stock.get('market_cap', 'N/A')})")
    else:
        print("   获取失败")
    
    # 测试所有交易所
    print("\n2. 测试所有交易所:")
    result = get_intrinio_stocks_all()
    if result:
        print(f"   获取到 {result['count']} 只唯一股票")
    else:
        print("   获取失败")


def test_with_filters():
    """测试筛选功能"""
    print("\n=== 测试筛选功能 ===")
    
    # 测试市值筛选
    print("\n1. 测试市值筛选 (市值 > 10000 百万美元):")
    result = get_intrinio_stocks(
        exchange="nasdaq",
        market_cap_min=10000
    )
    if result:
        print(f"   获取到 {result['count']} 只股票")
        if result["stocks"]:
            print("   前5只股票:")
            for stock in result["stocks"][:5]:
                print(f"     {stock['code']}: {stock['name']} (市值: {stock.get('market_cap', 'N/A')})")
    else:
        print("   获取失败")
    
    # 测试股价筛选
    print("\n2. 测试股价筛选 (股价在 50-100 美元之间):")
    result = get_intrinio_stocks(
        exchange="nyse",
        price_min=50,
        price_max=100
    )
    if result:
        print(f"   获取到 {result['count']} 只股票")
        if result["stocks"]:
            print("   前5只股票:")
            for stock in result["stocks"][:5]:
                print(f"     {stock['code']}: {stock['name']} (股价: {stock.get('price', 'N/A')})")
    else:
        print("   获取失败")
    
    # 测试行业筛选
    print("\n3. 测试行业筛选 (科技板块):")
    result = get_intrinio_stocks(
        exchange="nasdaq",
        sector="Technology"
    )
    if result:
        print(f"   获取到 {result['count']} 只股票")
        if result["stocks"]:
            print("   前5只股票:")
            for stock in result["stocks"][:5]:
                print(f"     {stock['code']}: {stock['name']} (行业: {stock.get('sector', 'N/A')})")
    else:
        print("   获取失败")


def test_combined_filters():
    """测试组合筛选"""
    print("\n=== 测试组合筛选 ===")
    
    # 测试组合筛选条件
    print("\n1. 测试组合筛选 (科技板块，市值 > 5000 百万美元):")
    result = get_intrinio_stocks_all(
        sector="Technology",
        market_cap_min=5000
    )
    if result:
        print(f"   获取到 {result['count']} 只股票")
        if result["stocks"]:
            print("   前5只股票:")
            for stock in result["stocks"][:5]:
                print(f"     {stock['code']}: {stock['name']} (市值: {stock.get('market_cap', 'N/A')}, 行业: {stock.get('sector', 'N/A')})")
    else:
        print("   获取失败")


def main():
    """主函数"""
    print("开始测试 Intrinio 数据源美股列表查询功能")
    print("=" * 60)
    
    try:
        # 测试基本功能
        test_basic_functionality()
        
        # 测试筛选功能
        test_with_filters()
        
        # 测试组合筛选
        test_combined_filters()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
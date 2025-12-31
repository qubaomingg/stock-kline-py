#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新集成的K线数据源功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.kline import get_kline_data


def test_eastmoney_hk():
    """测试香港股票的eastmoney数据源"""
    print("\n=== 测试香港股票eastmoney数据源 ===")
    
    # 测试腾讯控股 (00700)
    code = "00700"
    print(f"测试股票代码: {code}")
    
    result = get_kline_data(
        code=code,
        start_date="2024-01-01",
        end_date="2024-01-10",
        data_sources=['eastmoney_hk']  # 指定只使用eastmoney_hk
    )
    
    print(f"市场类型: {result.get('market')}")
    print(f"数据源: {result.get('data_source')}")
    print(f"数据条数: {len(result.get('data', []))}")
    
    if result.get('data'):
        print(f"第一条数据: {result['data'][0]}")
        print(f"最后一条数据: {result['data'][-1]}")
    
    return result


def test_eastmoney_cn():
    """测试A股股票的eastmoney数据源"""
    print("\n=== 测试A股股票eastmoney数据源 ===")
    
    # 测试平安银行 (000001)
    code = "000001"
    print(f"测试股票代码: {code}")
    
    result = get_kline_data(
        code=code,
        start_date="2024-01-01",
        end_date="2024-01-10",
        data_sources=['eastmoney_cn']  # 指定只使用eastmoney_cn
    )
    
    print(f"市场类型: {result.get('market')}")
    print(f"数据源: {result.get('data_source')}")
    print(f"数据条数: {len(result.get('data', []))}")
    
    if result.get('data'):
        print(f"第一条数据: {result['data'][0]}")
        print(f"最后一条数据: {result['data'][-1]}")
    
    return result


def test_default_sources():
    """测试默认数据源配置"""
    print("\n=== 测试默认数据源配置 ===")
    
    test_cases = [
        ("00700", "HK", "香港股票"),
        ("000001", "A", "A股股票"),
        ("TSLA", "US", "美股股票")
    ]
    
    for code, expected_market, description in test_cases:
        print(f"\n测试{description}: {code}")
        
        result = get_kline_data(
            code=code,
            start_date="2024-01-01",
            end_date="2024-01-10"
        )
        
        print(f"  市场类型: {result.get('market')} (期望: {expected_market})")
        print(f"  数据源: {result.get('data_source')}")
        print(f"  数据条数: {len(result.get('data', []))}")
        
        if result.get('error'):
            print(f"  错误信息: {result.get('error')}")
    
    return True


def main():
    """主测试函数"""
    print("开始测试新集成的K线数据源...")
    
    # 测试eastmoney_hk
    hk_result = test_eastmoney_hk()
    
    # 测试eastmoney_cn
    cn_result = test_eastmoney_cn()
    
    # 测试默认数据源配置
    test_default_sources()
    
    print("\n=== 测试完成 ===")
    
    # 总结
    print("\n测试总结:")
    print(f"1. eastmoney_hk数据源: {'成功' if hk_result.get('data') else '失败'}")
    print(f"2. eastmoney_cn数据源: {'成功' if cn_result.get('data') else '失败'}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
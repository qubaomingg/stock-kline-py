#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试obb.equity.screener的正确用法
"""

from openbb import obb
import pandas as pd

def test_screener():
    """测试screener功能"""
    try:
        print("测试obb.equity.screener...")
        
        # 使用yfinance作为provider
        result = obb.equity.screener(
            provider="yfinance",
            exchange="NASDAQ",
            type="stock"
        )
        
        print(f"结果类型: {type(result)}")
        print(f"结果属性: {[attr for attr in dir(result) if not attr.startswith('_')]}")
        
        if hasattr(result, 'results'):
            print(f"results类型: {type(result.results)}")
            if isinstance(result.results, pd.DataFrame):
                df = result.results
                print(f"数据形状: {df.shape}")
                print(f"数据列名: {df.columns.tolist()}")
                print(f"前5行数据:\n{df.head()}")
                return df
            else:
                print(f"results不是DataFrame: {result.results}")
        else:
            print("结果没有results属性")
            
        # 尝试to_df方法
        if hasattr(result, 'to_df'):
            df = result.to_df()
            print(f"to_df()结果形状: {df.shape}")
            print(f"to_df()前5行:\n{df.head()}")
            return df
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def test_screener_params():
    """测试不同的参数组合"""
    print("\n测试不同的参数组合...")
    
    test_cases = [
        {"provider": "yfinance", "exchange": "NASDAQ", "type": "stock"},
        {"provider": "yfinance", "exchange": "NYSE", "type": "stock"},
        {"provider": "yfinance", "exchange": "AMEX", "type": "stock"},
        {"provider": "fmp", "exchange": "NASDAQ", "type": "stock"},
        {"provider": "fmp", "exchange": "NYSE", "type": "stock"},
    ]
    
    for i, params in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {params}")
        try:
            result = obb.equity.screener(**params)
            if hasattr(result, 'results') and isinstance(result.results, pd.DataFrame):
                df = result.results
                print(f"  成功获取数据，形状: {df.shape}")
                print(f"  列名: {df.columns.tolist()}")
            elif hasattr(result, 'to_df'):
                df = result.to_df()
                print(f"  成功获取数据(to_df)，形状: {df.shape}")
            else:
                print(f"  获取结果类型: {type(result)}")
        except Exception as e:
            print(f"  失败: {e}")

if __name__ == "__main__":
    print(f"OpenBB版本: {obb.__version__ if hasattr(obb, '__version__') else 'unknown'}")
    print(f"obb.equity.screener类型: {type(obb.equity.screener)}")
    
    # 测试基本功能
    df = test_screener()
    
    # 测试不同参数
    test_screener_params()
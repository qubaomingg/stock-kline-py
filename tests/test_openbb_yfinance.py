#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试openbb-yfinance库的用法
"""

import asyncio
import pandas as pd
from openbb_yfinance import YFinanceEquityHistoricalFetcher

async def test_openbb_yfinance():
    """测试openbb-yfinance获取历史数据"""
    
    try:
        print("测试openbb-yfinance获取历史数据...")
        
        # 创建fetcher实例
        fetcher = YFinanceEquityHistoricalFetcher()
        
        # 准备参数
        params = {
            "symbol": "TSLA",
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
            "interval": "1d"
        }
        
        # 异步获取数据
        result = await fetcher.fetch_data(params=params)
        
        print(f"获取结果类型: {type(result)}")
        
        # 检查结果结构
        if hasattr(result, 'results'):
            print(f"results属性: {type(result.results)}")
            if isinstance(result.results, pd.DataFrame):
                print(f"数据形状: {result.results.shape}")
                print(f"数据列名: {result.results.columns.tolist()}")
                print(f"前几行数据:\n{result.results.head()}")
        
        # 尝试直接访问数据
        if hasattr(result, 'to_df'):
            df = result.to_df()
            print(f"to_df()结果形状: {df.shape}")
            print(f"to_df()前几行:\n{df.head()}")
        
        # 打印所有可用属性
        print("\n结果对象的所有属性:")
        for attr in dir(result):
            if not attr.startswith('_'):
                print(f"  {attr}: {type(getattr(result, attr))}")
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

async def test_other_params():
    """测试其他参数组合"""
    print("\n\n测试其他参数组合...")
    
    try:
        fetcher = YFinanceEquityHistoricalFetcher()
        
        # 测试不同的参数
        test_cases = [
            {"symbol": "AAPL", "start_date": "2024-01-01", "end_date": "2024-01-05"},
            {"symbol": "MSFT", "start_date": "2024-01-01", "interval": "1d"},
            {"symbol": "GOOGL", "start_date": "2024-01-01", "end_date": "2024-01-10", "interval": "1d"}
        ]
        
        for i, params in enumerate(test_cases):
            print(f"\n测试用例 {i+1}: {params}")
            try:
                result = await fetcher.fetch_data(params=params)
                if hasattr(result, 'results') and isinstance(result.results, pd.DataFrame):
                    print(f"  成功获取数据，形状: {result.results.shape}")
                else:
                    print(f"  获取结果类型: {type(result)}")
            except Exception as e:
                print(f"  失败: {e}")
                
    except Exception as e:
        print(f"测试其他参数时出错: {e}")

async def main():
    await test_openbb_yfinance()
    await test_other_params()

if __name__ == "__main__":
    asyncio.run(main())
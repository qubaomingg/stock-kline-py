#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试yfinance基本功能
"""

import yfinance as yf

print("测试yfinance基本功能...")

# 创建Ticker对象
ticker = yf.Ticker('TSLA')
print(f"Ticker对象创建成功: {ticker}")

# 获取历史数据
try:
    data = ticker.history(start='2024-12-01', end='2024-12-10')
    print(f"数据形状: {data.shape if data is not None else 'None'}")
    print(f"数据类型: {type(data)}")
    
    if data is not None and not data.empty:
        print(f"数据列名: {data.columns.tolist()}")
        print(f"前几行数据:\n{data.head()}")
        print(f"数据索引: {data.index}")
        print(f"数据信息:\n{data.info() if hasattr(data, 'info') else 'No info method'}")
    else:
        print("数据为空或None")
        
except Exception as e:
    print(f"获取数据时出错: {e}")
    import traceback
    traceback.print_exc()

# 测试其他股票代码
print("\n测试其他股票代码...")
for symbol in ['AAPL', 'MSFT', 'GOOGL']:
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        print(f"{symbol}: {data.shape if data is not None else 'None'}")
    except Exception as e:
        print(f"{symbol}: 错误 - {e}")
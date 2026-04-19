#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 finnhub 数据源使用 API Key
"""
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    print(f"加载环境变量文件: {env_path}")
    load_dotenv(env_path)
else:
    print("未找到 .env 文件")

api_key = os.getenv('FINNHUB_API_KEY')
print(f"FINNHUB_API_KEY: {api_key[:10]}..." if api_key else "未设置")

sys.path.insert(0, BASE_DIR)

from service.stocks.hk.finnhub_stocks import get_hk_stocks_by_finnhub

print("\n" + "=" * 70)
print("测试 finnhub 数据源")
print("=" * 70)

result = get_hk_stocks_by_finnhub()
if result and result.get('stocks'):
    print(f"\n✓ 成功! 股票数量: {result['count']}")
    print(f"数据源来源: {result.get('source', 'unknown')}")
    print("\n前 10 只股票:")
    for s in result['stocks'][:10]:
        print(f"  - {s.get('code', '')} - {s.get('name', '')}")
    print("\n后 10 只股票:")
    for s in result['stocks'][-10:]:
        print(f"  - {s.get('code', '')} - {s.get('name', '')}")
else:
    print("\n✗ 无数据返回")

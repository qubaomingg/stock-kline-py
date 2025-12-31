#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间参数是否被正确使用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.kline import get_kline_data

# 测试yfinance数据源
print("测试yfinance数据源...")
result = get_kline_data('000001', '2024-01-01', '2024-12-31', ['yfinance'])
print(f"结果类型: {type(result)}")
if result:
    print(f"数据源: {result.get('data_source')}")
    print(f"数据长度: {len(result.get('data', [])) if result.get('data') else 0}")
    if result.get('data'):
        print(f"第一条数据日期: {result['data'][0]['date'] if result['data'] else '无数据'}")
        print(f"最后一条数据日期: {result['data'][-1]['date'] if result['data'] else '无数据'}")
else:
    print("无结果")

print("\n测试baostock数据源...")
result = get_kline_data('000001', '2024-01-01', '2024-12-31', ['baostock'])
print(f"结果类型: {type(result)}")
if result:
    print(f"数据源: {result.get('data_source')}")
    print(f"数据长度: {len(result.get('data', [])) if result.get('data') else 0}")
    if result.get('data'):
        print(f"第一条数据日期: {result['data'][0]['date'] if result['data'] else '无数据'}")
        print(f"最后一条数据日期: {result['data'][-1]['date'] if result['data'] else '无数据'}")
else:
    print("无结果")

print("\n测试eastmoney_cn数据源...")
result = get_kline_data('000001', '2024-01-01', '2024-12-31', ['eastmoney_cn'])
print(f"结果类型: {type(result)}")
if result:
    print(f"数据源: {result.get('data_source')}")
    print(f"数据长度: {len(result.get('data', [])) if result.get('data') else 0}")
    if result.get('data'):
        print(f"第一条数据日期: {result['data'][0]['date'] if result['data'] else '无数据'}")
        print(f"最后一条数据日期: {result['data'][-1]['date'] if result['data'] else '无数据'}")
else:
    print("无结果")
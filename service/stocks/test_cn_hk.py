#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试cn和hk股票服务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cn.cn_stocks import get_cn_stocks
from hk.hk_stocks import get_hk_stocks

print("测试A股市场...")
try:
    cn_stocks = get_cn_stocks()
    print(f"  成功获取 {len(cn_stocks)} 只A股股票")
    print(f"  第一只股票: {cn_stocks[0]}")
except Exception as e:
    print(f"  获取失败: {e}")

print("\n测试港股市场...")
try:
    hk_stocks = get_hk_stocks()
    print(f"  成功获取 {len(hk_stocks)} 只港股")
    print(f"  第一只股票: {hk_stocks[0]}")
except Exception as e:
    print(f"  获取失败: {e}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试港股
"""
from service.stocks.hk.hk_stocks import get_hk_stocks

result = get_hk_stocks()
if result:
    print("✓ 成功！获取到", result["count"], "只港股")
    print("✓ 数据源:", result["source"])
    print("✓ 前 10 只:")
    for s in result["stocks"][:10]:
        print("  -", s["code"], "-", s["name"])
    print("\n✓ 后 10 只:")
    for s in result["stocks"][-10:]:
        print("  -", s["code"], "-", s["name"])
else:
    print("✗ 失败！")

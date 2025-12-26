#!/usr/bin/env python3
"""测试 intrinio 数据源"""

import sys
sys.path.insert(0, '.')

from service.stocks.us.us_stocks import get_us_stocks

print("测试 intrinio 数据源...")
result = get_us_stocks(data_source='intrinio')
print(f"Result type: {type(result)}")
if result:
    print(f"Result count: {result.get('count')}")
    print(f"Result has stocks: {len(result.get('stocks', []))}")
else:
    print("Result: None")
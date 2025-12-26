#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试港股服务资金流向数据获取
"""

import sys
sys.path.append('.')

from service.stock.hk.hk_service import get_hk_fund_flow_data

if __name__ == "__main__":
    print("测试港股服务资金流向数据获取...")
    
    result = get_hk_fund_flow_data()
    
    print(f"Result type: {type(result)}")
    
    if result:
        print(f"Has data: {'data' in result}")
        if 'data' in result:
            print(f"Data length: {len(result['data'])}")
            if len(result['data']) > 0:
                print(f"First data item: {result['data'][0]}")
    else:
        print("Result is None")
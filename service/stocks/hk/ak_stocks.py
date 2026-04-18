#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场 - akshare数据源
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import akshare as ak
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用SSL验证
original_requests_get = requests.get
def no_verify_get(*args, **kwargs):
    kwargs['verify'] = False
    return original_requests_get(*args, **kwargs)

requests.get = no_verify_get


def get_hk_stocks_by_ak() -> Optional[Dict[str, Any]]:
    """
    使用akshare获取港股市场所有股票列表

    Returns:
        包含港股股票列表的字典
    """
    try:
        print("[akshare] 尝试获取港股列表...")
        
        # 尝试多个akshare接口
        try:
            stock_hk_spot_em_df = ak.stock_hk_spot_em()
            if not stock_hk_spot_em_df.empty and '代码' in stock_hk_spot_em_df.columns and '名称' in stock_hk_spot_em_df.columns:
                print(f"[akshare] 使用 ak.stock_hk_spot_em() 成功")
                # 转换为列表格式
                stocks = []
                for _, row in stock_hk_spot_em_df.iterrows():
                    stock = {
                        'code': str(row['代码']),
                        'name': str(row['名称']),
                        'market': 'hk',
                        'full_code': f"{row['代码']}.HK",
                        'industry': '',  # 需要额外获取行业信息
                        'list_date': ''  # 需要额外获取上市日期
                    }
                    stocks.append(stock)
                result = {
                    'market': 'hk',
                    'count': len(stocks),
                    'stocks': stocks,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'akshare'
                }
                print(f"[akshare] 成功获取 {len(stocks)} 只港股")
                return result
        except Exception as e1:
            print(f"[akshare] 接口1失败: {e1}")
            
        # 尝试其他接口
        try:
            df = ak.stock_hk_name_code_em()
            if not df.empty and '代码' in df.columns and '名称' in df.columns:
                print(f"[akshare] 使用 ak.stock_hk_name_code_em() 成功")
                stocks = []
                for _, row in df.iterrows():
                    stock = {
                        'code': str(row['代码']),
                        'name': str(row['名称']),
                        'market': 'hk',
                        'full_code': f"{row['代码']}.HK",
                        'industry': '',
                        'list_date': ''
                    }
                    stocks.append(stock)
                return {
                    'market': 'hk',
                    'count': len(stocks),
                    'stocks': stocks,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'akshare'
                }
        except Exception as e2:
            print(f"[akshare] 接口2失败: {e2}")
            
        # 尝试另一个接口
        try:
            df = ak.stock_hk_spot()
            if not df.empty and '代码' in df.columns and '名称' in df.columns:
                print(f"[akshare] 使用 ak.stock_hk_spot() 成功")
                stocks = []
                for _, row in df.iterrows():
                    stock = {
                        'code': str(row['代码']),
                        'name': str(row['名称']),
                        'market': 'hk',
                        'full_code': f"{row['代码']}.HK",
                        'industry': '',
                        'list_date': ''
                    }
                    stocks.append(stock)
                return {
                    'market': 'hk',
                    'count': len(stocks),
                    'stocks': stocks,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'akshare'
                }
        except Exception as e3:
            print(f"[akshare] 接口3失败: {e3}")
        
        return None

    except Exception as e:
        print(f"[akshare] 获取港股股票列表时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = get_hk_stocks_by_ak()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只港股")
        print(f"数据源: {result['source']}")
        print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取港股股票列表失败")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国A股市场 - akshare数据源
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

# 尝试禁用urllib3的验证
original_urllib3_connection = urllib3.connectionpool.HTTPConnectionPool._make_request
def no_verify_connection(*args, **kwargs):
    kwargs['assert_hostname'] = False
    return original_urllib3_connection(*args, **kwargs)


def get_a_stocks_by_ak() -> Optional[Dict[str, Any]]:
    """
    使用akshare获取中国A股市场所有股票列表

    Returns:
        包含A股股票列表的字典
    """
    try:
        # 尝试不同的akshare接口
        print("[akshare] 尝试获取A股股票列表...")
        
        # 方法1: 尝试主要接口
        try:
            stock_info_a_code_name_df = ak.stock_info_a_code_name()
            if not stock_info_a_code_name_df.empty:
                print("[akshare] 成功使用 stock_info_a_code_name 接口")
                return _process_df(stock_info_a_code_name_df)
        except Exception as e1:
            print(f"[akshare] 接口1失败: {e1}")

        # 方法2: 尝试其他接口
        try:
            # 尝试另一个接口
            stock_list = []
            # 尝试获取A股列表
            # 先尝试上交所
            print("[akshare] 尝试获取上交所A股...")
            try:
                sh_df = ak.stock_info_sh_name_code()
                if not sh_df.empty:
                    for _, row in sh_df.iterrows():
                        stock_list.append({
                            'code': str(row['证券代码']),
                            'name': str(row['证券简称']),
                            'market': 'a',
                            'full_code': f"{row['证券代码']}.SH",
                            'industry': '',
                            'list_date': ''
                        })
            except Exception as sh_e:
                print(f"[akshare] 上交所接口失败: {sh_e}")

            # 再尝试深交所
            print("[akshare] 尝试获取深交所A股...")
            try:
                sz_df = ak.stock_info_sz_name_code()
                if not sz_df.empty:
                    for _, row in sz_df.iterrows():
                        stock_list.append({
                            'code': str(row['证券代码']),
                            'name': str(row['证券简称']),
                            'market': 'a',
                            'full_code': f"{row['证券代码']}.SZ",
                            'industry': '',
                            'list_date': ''
                        })
            except Exception as sz_e:
                print(f"[akshare] 深交所接口失败: {sz_e}")

            if len(stock_list) > 0:
                print(f"[akshare] 成功获取 {len(stock_list)} 只A股")
                return {
                    'market': 'a',
                    'count': len(stock_list),
                    'stocks': stock_list,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'akshare'
                }

        except Exception as e2:
            print(f"[akshare] 其他接口失败: {e2}")

        return None

    except Exception as e:
        print(f"[akshare] 获取A股股票列表时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def _process_df(df):
    """处理DataFrame返回结果"""
    stocks = []
    for _, row in df.iterrows():
        stock = {
            'code': str(row['code']),
            'name': str(row['name']),
            'market': 'a',
            'full_code': f"{row['code']}.SH" if row['code'].startswith('6') else f"{row['code']}.SZ",
            'industry': '',
            'list_date': ''
        }
        stocks.append(stock)

    return {
        'market': 'a',
        'count': len(stocks),
        'stocks': stocks,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'akshare'
    }


if __name__ == "__main__":
    result = get_a_stocks_by_ak()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只A股股票")
        print(f"数据源: {result['source']}")
        if result['stocks']:
            print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取A股股票列表失败")

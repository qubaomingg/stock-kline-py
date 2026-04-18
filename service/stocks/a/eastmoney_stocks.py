#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股市场 - eastmoney数据源
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from datetime import datetime
import time
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_a_stocks_by_eastmoney() -> Optional[Dict[str, Any]]:
    """
    直接调用东方财富API获取A股市场所有股票列表

    Returns:
        包含A股股票列表的字典
    """
    try:
        print("[eastmoney] 正在获取A股全列表...")

        # 先直接尝试使用akshare，比东方财富更可靠
        try:
            import akshare as ak
            print("[eastmoney] 优先使用akshare...")
            
            # 尝试多个akshare接口
            try:
                df = ak.stock_info_a_code_name()
                if not df.empty and 'code' in df.columns and 'name' in df.columns:
                    print(f"[eastmoney] akshare成功获取 {len(df)} 只股票")
                    stocks = []
                    for _, row in df.iterrows():
                        code = str(row['code'])
                        name = str(row['name'])
                        prefix = 'sh' if code.startswith('6') else 'sz'
                        stocks.append({
                            'code': code,
                            'name': name,
                            'market': 'a',
                            'full_code': f"{prefix}{code}",
                            'industry': '',
                            'list_date': ''
                        })
                    return {
                        'market': 'a',
                        'count': len(stocks),
                        'stocks': stocks,
                        'source': 'eastmoney+akshare',
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e1:
                print(f"[eastmoney] akshare接口1失败: {e1}")
                try:
                    df = ak.stock_zh_a_spot_em()
                    if not df.empty and '代码' in df.columns and '名称' in df.columns:
                        print(f"[eastmoney] akshare接口2成功获取 {len(df)} 只股票")
                        all_diffs = []
                        for _, row in df.iterrows():
                            all_diffs.append({'f12': str(row['代码']), 'f14': str(row['名称'])})
                        # 继续处理东方财富的解析逻辑
                except Exception as e2:
                    print(f"[eastmoney] akshare接口2也失败: {e2}")
                    pass  # 继续尝试东方财富API
        except Exception as e:
            print(f"[eastmoney] akshare不可用: {e}")
            pass  # 继续尝试东方财富API

        # 尝试东方财富API（作为备选）
        all_diffs = []
        try:
            print("[eastmoney] 尝试东方财富API...")
            endpoints = [
                "http://push2.eastmoney.com/api/qt/clist/get",
                "http://83.push2.eastmoney.com/api/qt/clist/get",
            ]

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Referer": "http://quote.eastmoney.com/",
            }

            params = {
                "pn": 1, "pz": 1000,
                "po": 1, "np": 1,
                "fltt": 2, "invt": 2, "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                "fields": "f12,f14",
            }

            for url in endpoints:
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
                    if response.status_code == 200:
                        data = response.json()
                        diffs = data.get("data", {}).get("diff", [])
                        if diffs:
                            all_diffs = diffs
                            print(f"[eastmoney] 东方财富API成功获取 {len(all_diffs)} 只股票")
                            break
                except Exception as e:
                    print(f"[eastmoney] 端点 {url} 失败: {e}")
                    continue
        except Exception as e:
            print(f"[eastmoney] 东方财富API异常: {e}")
            pass

        if not all_diffs:
            print("[eastmoney] 所有方法都失败")
            return None

        # 解析数据
        stocks = []
        for item in all_diffs:
            code = str(item.get('f12', ''))
            name = str(item.get('f14', ''))
            
            if not code or not name:
                continue

            if code.startswith(('60', '68')):
                prefix = 'sh'
            elif code.startswith(('00', '30')):
                prefix = 'sz'
            elif code.startswith('8'):
                prefix = 'bj'
            else:
                prefix = 'sh'

            stocks.append({
                'code': code,
                'name': name,
                'market': 'a',
                'full_code': f"{prefix}{code}",
                'industry': '',
                'list_date': ''
            })

        result = {
            'market': 'a',
            'count': len(stocks),
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'eastmoney'
        }

        print(f"[eastmoney] 成功获取 {len(stocks)} 只A股")
        return result

    except Exception as e:
        print(f"[eastmoney] 获取A股股票列表时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_a_stocks_by_eastmoney_with_env() -> Optional[Dict[str, Any]]:
    """
    使用环境变量配置的eastmoney数据源获取A股股票列表

    Returns:
        包含A股股票列表的字典
    """
    return get_a_stocks_by_eastmoney()


if __name__ == "__main__":
    result = get_a_stocks_by_eastmoney()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只A股")
        print(f"数据源: {result['source']}")
        if result['stocks']:
            print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取A股股票列表失败")

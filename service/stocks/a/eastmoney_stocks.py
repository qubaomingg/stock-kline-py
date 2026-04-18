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

        # 尝试不同的东方财富API端点
        endpoints = [
            "http://push2.eastmoney.com/api/qt/clist/get",
            "http://push2his.eastmoney.com/api/qt/clist/get",
            "http://83.push2.eastmoney.com/api/qt/clist/get",
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "http://quote.eastmoney.com/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

        # 尝试不同的参数组合
        params_list = [
            {
                "pn": 1, "pz": 5000,
                "po": 1, "np": 1, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": 2, "invt": 2, "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                "fields": "f12,f14",
            },
            {
                "pn": 1, "pz": 5000,
                "po": 1, "np": 1, "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "fltt": 2, "invt": 2, "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                "fields": "f12,f14",
            }
        ]

        all_diffs = []
        for url in endpoints:
            for params in params_list:
                try:
                    print(f"[eastmoney] 尝试 {url} ...")
                    response = requests.get(
                        url, params=params, headers=headers, timeout=20, verify=False
                    )
                    if response.status_code == 200:
                        data = response.json()
                        diffs = data.get("data", {}).get("diff", [])
                        if diffs:
                            all_diffs = diffs
                            print(f"[eastmoney] 成功获取 {len(all_diffs)} 只股票")
                            break
                except Exception as e:
                    print(f"[eastmoney] 端点失败: {e}")
                    continue
            if all_diffs:
                break

        # 如果东方财富API都失败了，尝试直接使用akshare
        if not all_diffs:
            print("[eastmoney] 东方财富API失败，尝试akshare...")
            try:
                import akshare as ak
                
                # 尝试多个akshare接口
                df = None
                try:
                    df = ak.stock_info_a_code_name()
                except Exception:
                    try:
                        df = ak.stock_zh_a_spot_em()
                        if not df.empty and '代码' in df.columns and '名称' in df.columns:
                            all_diffs = []
                            for _, row in df.iterrows():
                                all_diffs.append({'f12': str(row['代码']), 'f14': str(row['名称'])})
                    except Exception:
                        pass

                if df is not None and not df.empty and 'code' in df.columns and 'name' in df.columns:
                    print("[eastmoney] 使用akshare成功获取A股列表")
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
            except Exception as e:
                print(f"[eastmoney] akshare也失败: {e}")
                return None

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

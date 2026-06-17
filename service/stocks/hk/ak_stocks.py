#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场 - akshare 数据源
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import akshare as ak
import requests
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用 SSL 验证
original_requests_get = requests.get
def no_verify_get(*args, **kwargs):
    kwargs['verify'] = False
    return original_requests_get(*args, **kwargs)

requests.get = no_verify_get


def get_hk_stocks_by_ak() -> Optional[Dict[str, Any]]:
    """
    使用 akshare 获取港股市场所有股票列表

    Returns:
        包含港股股票列表的字典
    """
    try:
        print("[akshare] 正在获取港股...")

        df = None

        # 1. 先尝试 stock_hk_spot（可用，列名是 symbol 和 name）
        try:
            print("[akshare] 1. 尝试 stock_hk_spot...")
            df = ak.stock_hk_spot()
            if not df.empty:
                print(f"[akshare] stock_hk_spot 成功: {len(df)} 只")
        except Exception as e1:
            print(f"[akshare] 1. stock_hk_spot 失败: {e1}")

            # 2. 尝试直接东方财富 API
            try:
                print("[akshare] 2. 尝试东方财富 API...")
                url = "http://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    "pn": 1, "pz": 500,
                    "po": 1, "np": 1, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                    "fltt": 2, "invt": 2, "fid": "f3",
                    "fs": "m:128+t:3,m:128+t:4",
                    "fields": "f12,f14"
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Referer": "http://quote.eastmoney.com/",
                }
                response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    diffs = data.get("data", {}).get("diff", [])
                    if diffs:
                        print(f"[akshare] 东方财富 API 成功: {len(diffs)} 只")
                        df = pd.DataFrame(diffs)
                        df = df.rename(columns={'f12': 'symbol', 'f14': 'name'})
            except Exception as e2:
                print(f"[akshare] 2. 东方财富 API 也失败: {e2}")

        if df is None or df.empty:
            print("[akshare] 所有方法都失败")
            return None

        # 港股非股票类型关键词（权证/衍生品/基金/债券/ETF等）
        NON_STOCK_KEYWORDS = [
            '购', '沽', '权证', '牛', '熊',
            '基金', 'ETF', 'ETF-R', 'ETP', '信托', '债券', '债',
            '指数', '期货', '期权', 'REIT', 'reit',
            '优先', '存托', 'A', 'B',
            '现金', '黄金', '白银', '人民币', '港元',
        ]
        
        def _is_valid_hk_stock(name: str, code: str) -> bool:
            """判断是否为有效港股（过滤权证/基金/衍生品）"""
            if not name or name == 'nan':
                return False
            name_upper = name.upper()
            for kw in NON_STOCK_KEYWORDS:
                if kw in name_upper:
                    return False
            # 港股代码应为 5 位数字
            if not code.isdigit() or len(code) < 4 or len(code) > 5:
                return False
            return True

        # 转换为列表格式
        stocks = []
        filtered_out = 0
        for _, row in df.iterrows():
            code = str(row['symbol'])
            name = str(row['name'])

            if not code or not name:
                continue

            if code and code.isdigit():
                code = code.zfill(5)

            # 应用名称过滤
            if not _is_valid_hk_stock(name, code):
                filtered_out += 1
                continue

            stock = {
                'code': code,
                'name': name,
                'market': 'hk',
                'full_code': f"{code}.HK",
                'industry': '',
                'list_date': ''
            }
            stocks.append(stock)

        result = {
            'market': 'hk',
            'count': len(stocks),
            'filtered_out': filtered_out,
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'akshare'
        }

        print(f"[akshare] 成功获取 {len(stocks)} 只港股，过滤掉 {filtered_out} 只非股票")
        return result

    except Exception as e:
        print(f"[akshare] 获取港股时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = get_hk_stocks_by_ak()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只港股")
        print(f"数据源: {result['source']}")
        if result['stocks']:
            print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取港股股票列表失败")

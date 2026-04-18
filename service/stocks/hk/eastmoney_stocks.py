#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场 - 东方财富数据源
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from datetime import datetime
import time
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_hk_stocks_by_eastmoney() -> Optional[Dict[str, Any]]:
    """
    直接调用东方财富API获取港股市场所有股票列表

    Returns:
        包含港股股票列表的字典
    """
    try:
        print("[eastmoney] 正在获取港股...")
        
        # 尝试多个东方财富API端点
        endpoints = [
            "http://push2.eastmoney.com/api/qt/clist/get",
            "http://83.push2.eastmoney.com/api/qt/clist/get"
        ]
        
        params = {
            "pn": 1, "pz": 500,  # 一次获取500条
            "po": 1, "np": 1, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2, "invt": 2, "fid": "f3", 
            "fs": "m:128+t:3,m:128+t:4",  # 港股主板+创业板
            "fields": "f12,f14",  # 只需要代码和名称
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "http://quote.eastmoney.com/",
        }
        
        all_diffs = []
        
        for url in endpoints:
            try:
                print(f"[eastmoney] 尝试 {url}...")
                response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
                
                if response.status_code == 200:
                    data = response.json()
                    diffs = data.get("data", {}).get("diff", [])
                    
                    if diffs:
                        all_diffs = diffs
                        print(f"[eastmoney] 从 {url} 成功获取 {len(all_diffs)} 只股票")
                        break
            except Exception as e:
                print(f"[eastmoney] 端点失败: {e}")
                continue
        
        if not all_diffs:
            print("[eastmoney] 东方财富API都失败，尝试直接用 akshare...")
            try:
                import akshare as ak
                try:
                    df = ak.stock_hk_spot()
                    if not df.empty and '代码' in df.columns and '名称' in df.columns:
                        all_diffs = []
                        for _, row in df.iterrows():
                            all_diffs.append({
                                'f12': str(row['代码']), 
                                'f14': str(row['名称'])
                            })
                        print(f"[eastmoney] 从 ak.stock_hk_spot() 获取 {len(all_diffs)} 只股票")
                except Exception:
                    try:
                        df = ak.stock_hk_spot_em()
                        if not df.empty and '代码' in df.columns and '名称' in df.columns:
                            all_diffs = []
                            for _, row in df.iterrows():
                                all_diffs.append({
                                    'f12': str(row['代码']), 
                                    'f14': str(row['名称'])
                                })
                            print(f"[eastmoney] 从 ak.stock_hk_spot_em() 获取 {len(all_diffs)} 只股票")
                    except Exception as e2:
                        print(f"[eastmoney] akshare也失败: {e2}")
            except Exception as e:
                print(f"[eastmoney] akshare 导入失败: {e}")
        
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
            
            # 港股代码格式化
            if len(code) < 5:
                code = code.zfill(5)
            
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
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'eastmoney'
        }
        
        print(f"[eastmoney] 港股获取成功，共 {len(stocks)} 只股票")
        return result

    except Exception as e:
        print(f"[eastmoney] 获取港股时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_hk_stocks_by_eastmoney_with_env() -> Optional[Dict[str, Any]]:
    """
    兼容旧接口

    Returns:
        包含港股股票列表的字典
    """
    return get_hk_stocks_by_eastmoney()


if __name__ == "__main__":
    result = get_hk_stocks_by_eastmoney()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只港股")
        print(f"数据源: {result['source']}")
        if result['stocks']:
            print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取港股股票列表失败")

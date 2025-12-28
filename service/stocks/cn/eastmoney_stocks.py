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


def get_cn_stocks_by_eastmoney() -> Optional[Dict[str, Any]]:
    """
    直接调用东方财富API获取A股市场所有股票列表
    
    Returns:
        包含A股股票列表的字典
    """
    try:
        print("[eastmoney] 正在获取A股全列表...")
        
        # 直接调用东方财富API获取A股列表
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        
        # 先获取第一页数据，了解总数
        # A股的fs参数：m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23
        # 包含：沪深主板、科创板、创业板、北交所等
        params = {
            "pn": 1, "pz": 100,  # 每页100条（API限制）
            "po": 1, "np": 1, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2, "invt": 2, "fid": "f3", 
            "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23",  # A股主板、科创板、创业板等
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        total = data.get("data", {}).get("total", 0)
        print(f"[eastmoney] A股总数: {total}只")
        
        if total == 0:
            print("[eastmoney] 获取A股股票列表失败: 数据为空")
            return None
        
        # 收集所有数据
        all_diffs = []
        all_diffs.extend(data["data"]["diff"])
        
        # 计算需要多少页（每页100条）
        pages_needed = (total + 99) // 100  # 向上取整
        
        if pages_needed > 1:
            print(f"[eastmoney] 需要分页获取，共{pages_needed}页")
            
            for page in range(2, pages_needed + 1):
                params["pn"] = page
                print(f"[eastmoney] 正在获取第{page}/{pages_needed}页...")
                
                response = requests.get(url, params=params)
                page_data = response.json()
                
                if page_data.get("data", {}).get("diff"):
                    all_diffs.extend(page_data["data"]["diff"])
                
                # 避免请求过快
                time.sleep(0.1)
        
        # 解析所有数据
        df = pd.DataFrame(all_diffs)
        
        if df.empty:
            print("[eastmoney] 获取A股股票列表失败: 数据为空")
            return None
        
        # 字段映射（标准化）
        df.rename(columns={
            "f12": "symbol",  # 股票代码
            "f14": "name",    # 股票名称
            "f2": "price",    # 当前价格
            "f3": "price_change_pct",  # 涨跌幅
            "f18": "market_cap"  # 市值
        }, inplace=True)
        
        # 核心清洗步骤
        df_clean = (
            df.drop_duplicates(subset=["symbol"])  # 按股票代码去重
            .dropna(subset=["symbol", "name", "price"])  # 删除关键字段为空的行
            .reset_index(drop=True)  # 重置索引
        )
        
        # 标准化字段（统一单位/格式）
        df_clean["price"] = pd.to_numeric(df_clean["price"], errors="coerce")  # 价格转数值
        df_clean["market_cap"] = pd.to_numeric(df_clean["market_cap"], errors="coerce")  # 市值转数值
        df_clean["symbol"] = df_clean["symbol"].str.strip()  # 去除代码前后空格
        
        # 转换为列表格式
        stocks = []
        for _, row in df_clean.iterrows():
            # 判断沪深交易所
            symbol_str = str(row['symbol'])
            if symbol_str.startswith(('60', '68')):
                full_code = f"{symbol_str}.SH"  # 上海主板/科创板
            elif symbol_str.startswith(('00', '30')):
                full_code = f"{symbol_str}.SZ"  # 深圳主板/创业板
            elif symbol_str.startswith('8'):
                full_code = f"{symbol_str}.BJ"  # 北交所
            else:
                full_code = f"{symbol_str}.CN"  # 其他
                
            stock = {
                'code': symbol_str,
                'name': str(row['name']),
                'market': 'cn',
                'full_code': full_code,
                'industry': '',  # 东方财富API不提供行业信息
                'list_date': ''  # 需要额外获取上市日期
            }
            stocks.append(stock)
        
        result = {
            'market': 'cn',
            'count': len(stocks),
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'eastmoney'
        }
        
        print(f"[eastmoney] A股全列表清洗完成，共{len(stocks)}只标的")
        return result
        
    except Exception as e:
        print(f"[eastmoney] 获取A股股票列表时发生错误: {e}")
        return None


def get_cn_stocks_by_eastmoney_with_env() -> Optional[Dict[str, Any]]:
    """
    使用环境变量配置的eastmoney数据源获取A股股票列表
    
    Returns:
        包含A股股票列表的字典
    """
    # eastmoney不需要API密钥，直接调用
    return get_cn_stocks_by_eastmoney()


if __name__ == "__main__":
    result = get_cn_stocks_by_eastmoney()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只A股")
        print(f"数据源: {result['source']}")
        print(f"时间戳: {result['timestamp']}")
        if result['stocks']:
            print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取A股股票列表失败")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场股票列表服务
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import akshare as ak


def get_hk_stocks() -> Optional[Dict[str, Any]]:
    """
    获取港股市场所有股票列表
    
    Returns:
        包含港股股票列表的字典
    """
    try:
        # 使用akshare获取港股股票列表
        stock_hk_spot_em_df = ak.stock_hk_spot_em()
        
        if stock_hk_spot_em_df.empty:
            print("获取港股股票列表失败: 数据为空")
            return None
        
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
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
        
    except Exception as e:
        print(f"获取港股股票列表时发生错误: {e}")
        return None


if __name__ == "__main__":
    result = get_hk_stocks()
    if result:
        print(f"获取到 {result['count']} 只港股")
        print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("获取港股股票列表失败")
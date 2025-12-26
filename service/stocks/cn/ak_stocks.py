#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国A股市场 - akshare数据源
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import akshare as ak


def get_cn_stocks_by_ak() -> Optional[Dict[str, Any]]:
    """
    使用akshare获取中国A股市场所有股票列表
    
    Returns:
        包含A股股票列表的字典
    """
    try:
        # 使用akshare获取A股股票列表
        stock_info_a_code_name_df = ak.stock_info_a_code_name()
        
        if stock_info_a_code_name_df.empty:
            print("[akshare] 获取A股股票列表失败: 数据为空")
            return None
        
        # 转换为列表格式
        stocks = []
        for _, row in stock_info_a_code_name_df.iterrows():
            stock = {
                'code': str(row['code']),
                'name': str(row['name']),
                'market': 'cn',
                'full_code': f"{row['code']}.SH" if row['code'].startswith('6') else f"{row['code']}.SZ",
                'industry': '',  # 需要额外获取行业信息
                'list_date': ''  # 需要额外获取上市日期
            }
            stocks.append(stock)
        
        result = {
            'market': 'cn',
            'count': len(stocks),
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'akshare'
        }
        
        print(f"[akshare] 成功获取 {len(stocks)} 只A股股票")
        return result
        
    except Exception as e:
        print(f"[akshare] 获取A股股票列表时发生错误: {e}")
        return None


if __name__ == "__main__":
    result = get_cn_stocks_by_ak()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只A股股票")
        print(f"数据源: {result['source']}")
        print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取A股股票列表失败")
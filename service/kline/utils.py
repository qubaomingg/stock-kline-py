#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据处理工具模块
包含通用的数据处理函数，避免循环导入
"""

from typing import Dict, List
import pandas as pd


def process_kline_data(data: pd.DataFrame, source: str) -> List[Dict]:
    """
    处理K线数据，统一格式
    
    Args:
        data: 原始数据DataFrame
        source: 数据源名称
        
    Returns:
        处理后的数据列表
    """
    if data.empty:
        return []
    
    # 确保有日期列
    if 'date' not in data.columns and data.index.name == 'date':
        data = data.reset_index()
    
    # 统一列名映射
    column_mapping = {
        'open': ['open', 'Open', 'OPEN', '开盘'],
        'high': ['high', 'High', 'HIGH', '最高'],
        'low': ['low', 'Low', 'LOW', '最低'],
        'close': ['close', 'Close', 'CLOSE', 'last', '收盘'],
        'volume': ['volume', 'Volume', 'VOLUME', 'vol', '成交量'],
        'date': ['date', 'Date', 'DATE', 'datetime', 'time', '日期']
    }
    
    # 重命名列
    for target_col, possible_cols in column_mapping.items():
        for col in possible_cols:
            if col in data.columns:
                if col != target_col:
                    data = data.rename(columns={col: target_col})
                break
    
    # 确保必要的列存在
    required_cols = ['date', 'open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in data.columns:
            print(f"警告: {source} 数据源缺少 {col} 列")
            return []
    
    # 转换日期格式
    data['date'] = pd.to_datetime(data['date'])
    
    # 转换为字典列表
    result = []
    for _, row in data.iterrows():
        item = {
            'date': row['date'].strftime('%Y-%m-%d'),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        }
        
        # 添加成交量（如果有）
        if 'volume' in data.columns:
            item['volume'] = int(row['volume']) if pd.notna(row['volume']) else 0
        
        result.append(item)
    
    return result
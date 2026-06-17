#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据处理工具模块
包含通用的数据处理函数，避免循环导入
"""

import logging
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def _to_json_value(val: Any, field_name: str = '') -> Any:
    """
    将 pandas/numpy 类型转换为可 JSON 序列化的 Python 原生类型

    Args:
        val: 待转换的值
        field_name: 字段名（用于调试日志）

    Returns:
        可 JSON 序列化的值 (str/int/float/None 等)
    """
    # 1. 处理 None/NaN
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass

    # 2. 处理日期类型：转为 "YYYY-MM-DD" 字符串
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        try:
            return pd.Timestamp(val).strftime('%Y-%m-%d')
        except Exception:
            return str(val)

    # 3. 处理数值类型：确保是原生 Python int/float，并拦截 NaN/Inf
    # numpy 数值
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        fv = float(val)
        if math.isnan(fv) or math.isinf(fv):
            return None
        return fv

    # Python 原生数值
    if isinstance(val, bool):
        return bool(val)
    if isinstance(val, int):
        return int(val)
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val

    # 4. 字符串
    if isinstance(val, str):
        return val

    # 5. 其他类型，先尝试转字符串
    try:
        return str(val)
    except Exception:
        return None


def process_kline_data(data: pd.DataFrame, source: str) -> List[Dict]:
    """
    处理K线数据，统一格式，并确保所有值是可 JSON 序列化的 Python 原生类型

    Args:
        data: 原始数据DataFrame
        source: 数据源名称

    Returns:
        处理后的数据列表
    """
    if data is None or data.empty:
        return []

    # 确保有日期列
    if 'date' not in data.columns and data.index.name in ('date', 'Date', 'Date'):
        data = data.reset_index()
    elif 'date' not in data.columns:
        # 如果 index 没有 name 但确实是日期型
        data = data.reset_index()
        # reset_index 后会出现名为 'index' 的列，尝试把它当日期列
        if 'index' in data.columns:
            data = data.rename(columns={'index': 'date'})

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
            logger.warning(f"{source} 数据源缺少 {col} 列，可用列: {list(data.columns)}")
            return []

    # 转换为字典列表（严格确保每个值都是 Python 原生类型）
    result = []
    for _, row in data.iterrows():
        # 日期：转为 "YYYY-MM-DD" 字符串
        date_val = row['date']
        try:
            if isinstance(date_val, (pd.Timestamp, np.datetime64)):
                date_str = pd.Timestamp(date_val).strftime('%Y-%m-%d')
            elif hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                # 可能是字符串，直接使用
                parsed = pd.to_datetime(str(date_val), errors='coerce')
                if pd.isna(parsed):
                    continue  # 无法解析日期，跳过这一行
                date_str = parsed.strftime('%Y-%m-%d')
        except Exception:
            continue

        # 数值：确保是 float，并过滤 NaN
        try:
            o = float(row['open'])
            h = float(row['high'])
            l = float(row['low'])
            c = float(row['close'])
            if any(math.isnan(v) or math.isinf(v) for v in (o, h, l, c)):
                continue
        except (ValueError, TypeError):
            continue

        item = {
            'date': date_str,
            'open': o,
            'high': h,
            'low': l,
            'close': c,
        }

        # 成交量：确保是 int，NaN 转 0
        if 'volume' in data.columns:
            try:
                v = row['volume']
                if pd.notna(v) and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                    item['volume'] = int(v)
                else:
                    item['volume'] = 0
            except (ValueError, TypeError):
                item['volume'] = 0

        result.append(item)

    return result
